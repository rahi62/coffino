from .shared import *
from .shared import BaseVS, _branch_accessible

class HallVS(BaseVS): queryset=Hall.objects.all(); serializer_class=HallSerializer; cafino_write_permission='tables.use'; cafino_read_permission=('tables.use', 'orders.create')

class TableVS(BaseVS):
    cafino_read_permission=('tables.use', 'orders.create')
    cafino_write_permission='tables.use'
    queryset=Table.objects.select_related("hall__branch").all()
    serializer_class=TableSerializer

    @action(detail=True,methods=["post"])
    @transaction.atomic
    def open_session(self,request,pk=None):
        if not has_perm(request.user,'tables.use'):
            return Response({"detail":"دسترسی ندارید"},status=403)
        scoped=self.get_object()
        table=Table.objects.select_for_update().get(pk=scoped.pk)
        if table.sessions.filter(is_open=True).exists():
            return Response({"detail":"میز جلسه باز دارد"},status=409)
        session=TableSession.objects.create(
            table=table,customer_count=request.data.get("customer_count",1),opened_by=request.user
        )
        table.status=Table.Status.OCCUPIED
        table.save(update_fields=["status","updated_at"])
        return Response(TableSessionSerializer(session).data,status=201)

    @action(detail=True,methods=["post"])
    @transaction.atomic
    def close_session(self,request,pk=None):
        if not has_perm(request.user,'tables.use'):
            return Response({"detail":"دسترسی ندارید"},status=403)
        scoped=self.get_object()
        table=Table.objects.select_for_update().get(pk=scoped.pk)
        session=table.sessions.filter(is_open=True).first()
        if not session:
            return Response({"detail":"جلسه بازی وجود ندارد"},status=404)
        if session.orders.exclude(status__in=[Order.Status.COMPLETED,Order.Status.CANCELLED]).exists():
            return Response({"detail":"سفارش باز وجود دارد"},status=409)
        session.is_open=False
        session.closed_at=timezone.now()
        session.save(update_fields=["is_open","closed_at","updated_at"])
        try:
            from apps.reservations.models import Reservation
            has_reservation=Reservation.objects.filter(
                table=table,status__in=[Reservation.Status.PENDING,Reservation.Status.CONFIRMED],
                reserved_for__gte=timezone.now()
            ).exists()
        except Exception:
            has_reservation=False
        table.status=Table.Status.RESERVED if has_reservation else Table.Status.FREE
        table.save(update_fields=["status","updated_at"])
        return Response(TableSessionSerializer(session).data)

class TableSessionVS(BaseVS):
    cafino_read_permission=('tables.use', 'orders.create')
    cafino_write_permission='tables.use'
    queryset=TableSession.objects.select_related("table").all()
    serializer_class=TableSessionSerializer
    filterset_fields=["is_open","table"]

class OrderVS(BaseVS):
    cafino_read_permission='orders.view'
    queryset=Order.objects.select_related("branch","table_session__table").prefetch_related(
        "items__product__preparation_station","payments"
    ).all()
    serializer_class=OrderSerializer
    filterset_fields=["branch","order_type","status","payment_status"]

    def create(self,request,*args,**kwargs):
        return Response({'detail':'برای ایجاد سفارش از /checkout/ استفاده کنید'},status=405)
    def update(self,request,*args,**kwargs):
        return Response({'detail':'ویرایش مستقیم Order مجاز نیست'},status=405)
    def partial_update(self,request,*args,**kwargs):
        return Response({'detail':'ویرایش مستقیم Order مجاز نیست'},status=405)
    def destroy(self,request,*args,**kwargs):
        return Response({'detail':'حذف Order مجاز نیست؛ از Void استفاده کنید'},status=405)

    @action(detail=True,methods=["post"])
    def mark_ready(self,request,pk=None):
        if not has_perm(request.user,'kitchen.update'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        o=self.get_object()
        o.status=Order.Status.READY
        o.save(update_fields=["status","updated_at"])
        o.kitchen_tickets.update(status=KitchenTicket.Status.READY)
        from apps.notifications.services import enqueue_order_ready
        enqueue_order_ready(o)
        return Response(self.get_serializer(o).data)

    @action(detail=True,methods=["post"])
    def complete(self,request,pk=None):
        if not has_perm(request.user,'orders.complete'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        o=self.get_object()
        if o.payment_status not in [
            Order.PaymentStatus.PAID,Order.PaymentStatus.PARTIALLY_REFUNDED,Order.PaymentStatus.REFUNDED
        ]:
            return Response({"detail":"سفارش قبل از تکمیل باید تسویه شود"},status=409)
        o.status=Order.Status.COMPLETED
        o.save(update_fields=["status","updated_at"])
        o.kitchen_tickets.update(status=KitchenTicket.Status.DONE)
        from apps.loyalty.services import earn_order_points
        earn_order_points(o)
        try:
            x=o.online_order
            x.status=OnlineOrder.Status.COMPLETED
            x.save(update_fields=['status','updated_at'])
        except Exception:
            pass
        return Response(self.get_serializer(o).data)

    @action(detail=True,methods=["post"])
    def cancel(self,request,pk=None):
        from apps.accounts.override import validate_override
        order=self.get_object()
        manager=request.user if has_perm(request.user,'orders.void') else validate_override(
            request.headers.get('X-Cafino-Override'),branch=order.branch,permission_code='orders.void'
        )
        if not manager:
            return Response({"detail":"Void نیازمند تأیید مدیر است"},status=403)
        try:
            o=void_order(order,user=manager,reason=request.data.get("reason","لغو سفارش"))
        except ValueError as e:
            return Response({"detail":str(e)},status=409)
        return Response(self.get_serializer(o).data)

    @action(detail=True,methods=["post"])
    def refund(self,request,pk=None):
        from apps.accounts.override import validate_override
        order=self.get_object()
        manager=request.user if has_perm(request.user,'payments.refund') else validate_override(
            request.headers.get('X-Cafino-Override'),branch=order.branch,permission_code='payments.refund'
        )
        if not manager:
            return Response({"detail":"Refund نیازمند تأیید مدیر است"},status=403)
        try:
            rows=refund_order(
                order,amount=request.data.get("amount"),user=manager,
                reason=request.data.get("reason","برگشت وجه"),method=request.data.get("method")
            )
        except (ValueError,TypeError) as e:
            return Response({"detail":str(e)},status=400)
        return Response(
            {"refunds":RefundSerializer(rows,many=True).data,
             "total":sum((x.amount for x in rows),Decimal('0'))},
            status=201
        )

class PaymentVS(viewsets.ReadOnlyModelViewSet):
    permission_classes=[permissions.IsAuthenticated]
    queryset=Payment.objects.prefetch_related("refunds").select_related("order__branch").all()
    serializer_class=PaymentSerializer

    def get_queryset(self):
        qs=super().get_queryset()
        if not (has_perm(self.request.user,'orders.view') or has_perm(self.request.user,'reports.view')):
            return qs.none()
        return scope_queryset(
            qs,self.request.user,
            branch_path='order__branch',business_path='order__branch__business'
        )

class RefundVS(viewsets.ReadOnlyModelViewSet):
    permission_classes=[permissions.IsAuthenticated]
    queryset=Refund.objects.select_related("payment__order__branch").all()
    serializer_class=RefundSerializer

    def get_queryset(self):
        qs=super().get_queryset()
        if not (has_perm(self.request.user,'payments.refund') or has_perm(self.request.user,'reports.view')):
            return qs.none()
        return scope_queryset(
            qs,self.request.user,
            branch_path='payment__order__branch',business_path='payment__order__branch__business'
        )

class StationVS(BaseVS):
    cafino_read_permission=('kitchen.view', 'inventory.manage')
    cafino_write_permission='kitchen.update'
    queryset=PreparationStation.objects.all()
    serializer_class=PreparationStationSerializer

class KitchenTicketVS(BaseVS):
    cafino_read_permission='kitchen.view'
    queryset=KitchenTicket.objects.select_related("order__branch","station").prefetch_related(
        "order__items__product__preparation_station"
    ).all()
    serializer_class=KitchenTicketSerializer
    filterset_fields=["station","status"]

    @action(detail=True,methods=["post"])
    def preparing(self,request,pk=None):
        if not has_perm(request.user,'kitchen.update'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        t=self.get_object()
        t.status=KitchenTicket.Status.PREPARING
        t.save(update_fields=["status","updated_at"])
        return Response(self.get_serializer(t).data)

    @action(detail=True,methods=["post"])
    def ready(self,request,pk=None):
        if not has_perm(request.user,'kitchen.update'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        t=self.get_object()
        t.status=KitchenTicket.Status.READY
        t.save(update_fields=["status","updated_at"])
        if not t.order.kitchen_tickets.exclude(status=KitchenTicket.Status.READY).exists():
            t.order.status=Order.Status.READY
            t.order.save(update_fields=["status","updated_at"])
            from apps.notifications.services import enqueue_order_ready
            enqueue_order_ready(t.order)
            try:
                x=t.order.online_order
                x.status='READY'
                x.save(update_fields=['status','updated_at'])
            except Exception:
                pass
        return Response(self.get_serializer(t).data)

class PagerVS(BaseVS):
    cafino_read_permission=('orders.view', 'orders.create')
    cafino_write_permission='orders.create'
    queryset=PagerDevice.objects.all()
    serializer_class=PagerDeviceSerializer

class TakeawayProfileVS(BaseVS):
    cafino_read_permission=('orders.view', 'orders.create')
    cafino_write_permission='orders.create'
    queryset=TakeawayProfile.objects.select_related("pager__branch","order__branch").all()
    serializer_class=TakeawayProfileSerializer

    @action(detail=True,methods=["post"])
    def assign_pager(self,request,pk=None):
        if not has_perm(request.user,'orders.create'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        x=self.get_object()
        pager=get_object_or_404(
            PagerDevice.objects.select_related('branch'),
            pk=request.data.get("pager_id"),status=PagerDevice.Status.AVAILABLE
        )
        if pager.branch_id!=x.order.branch_id:
            return Response({'detail':'پیجر متعلق به شعبه سفارش نیست'},status=400)
        if x.pager_id:
            return Response({"detail":"پیجر قبلاً اختصاص داده شده"},status=409)
        x.pager=pager
        x.save(update_fields=["pager","updated_at"])
        pager.status=PagerDevice.Status.ASSIGNED
        pager.save(update_fields=["status","updated_at"])
        return Response(self.get_serializer(x).data)

    @action(detail=True,methods=["post"])
    def release_pager(self,request,pk=None):
        if not has_perm(request.user,'orders.create'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        x=self.get_object()
        pager=x.pager
        if pager:
            pager.status=PagerDevice.Status.AVAILABLE
            pager.save(update_fields=["status","updated_at"])
        x.pager=None
        x.save(update_fields=["pager","updated_at"])
        return Response(self.get_serializer(x).data)

class ReservationVS(viewsets.ModelViewSet):
    serializer_class=ReservationSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=Reservation.objects.select_related('branch','table__hall__branch','customer','seated_session').all()
        if not has_perm(self.request.user,'reservations.manage'):
            return qs.none()
        return scope_queryset(qs,self.request.user,branch_path='branch',business_path='branch__business')

    def update(self,request,*args,**kwargs):
        return Response({'detail':'از Actionهای رزرو استفاده کنید'},status=405)

    def partial_update(self,request,*args,**kwargs):
        return Response({'detail':'از Actionهای رزرو استفاده کنید'},status=405)

    def destroy(self,request,*args,**kwargs):
        return Response({'detail':'حذف مستقیم رزرو مجاز نیست'},status=405)

    def create(self,request,*args,**kwargs):
        if not has_perm(request.user,'reservations.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            branch=resolve_branch_for_user(request.user,request.data.get('branch'))
        except Exception:
            return Response({'detail':'شعبه رزرو معتبر نیست'},status=403)

        table=None
        if request.data.get('table'):
            table=get_object_or_404(Table.objects.select_related('hall__branch'),pk=request.data.get('table'))
            if table.hall.branch_id!=branch.id:
                return Response({'detail':'میز متعلق به شعبه رزرو نیست'},status=400)

        customer=None
        if request.data.get('customer'):
            customer=get_object_or_404(Customer,pk=request.data.get('customer'))
            if customer.branch_id!=branch.id:
                return Response({'detail':'مشتری متعلق به شعبه رزرو نیست'},status=400)

        try:
            r=create_reservation(
                branch=branch,customer_name=request.data.get('customer_name',''),
                phone=request.data.get('phone',''),party_size=int(request.data.get('party_size',2)),
                reserved_for=request.data.get('reserved_for'),
                duration_minutes=int(request.data.get('duration_minutes',90)),
                table=table,customer=customer,source=request.data.get('source','STAFF'),
                notes=request.data.get('notes',''),user=request.user
            )
        except (ValueError,TypeError) as e:
            return Response({'detail':str(e)},status=400)
        return Response(self.get_serializer(r).data,status=201)

    @action(detail=True,methods=['post'])
    def confirm(self,request,pk=None):
        if not has_perm(request.user,'reservations.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        r=self.get_object()
        r.status=Reservation.Status.CONFIRMED
        r.save(update_fields=['status','updated_at'])
        return Response(self.get_serializer(r).data)

    @action(detail=True,methods=['post'])
    def cancel(self,request,pk=None):
        if not has_perm(request.user,'reservations.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        r=self.get_object()
        r.status=Reservation.Status.CANCELLED
        r.save(update_fields=['status','updated_at'])
        if r.table_id and not r.table.sessions.filter(is_open=True).exists() and not Reservation.objects.filter(
            table=r.table,status__in=[Reservation.Status.PENDING,Reservation.Status.CONFIRMED],
            reserved_for__gte=timezone.now()
        ).exclude(pk=r.pk).exists():
            r.table.status=Table.Status.FREE
            r.table.save(update_fields=['status','updated_at'])
        return Response(self.get_serializer(r).data)

    @action(detail=True,methods=['post'])
    def seat(self,request,pk=None):
        if not has_perm(request.user,'reservations.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            r=seat_reservation(self.get_object(),user=request.user)
        except ValueError as e:
            return Response({'detail':str(e)},status=409)
        return Response(self.get_serializer(r).data)

class OnlineMenuSettingsVS(BaseVS):
    cafino_read_permission='online_ordering.manage'
    cafino_write_permission='online_ordering.manage'
    queryset=OnlineMenuSettings.objects.select_related('branch').all();serializer_class=OnlineMenuSettingsSerializer
    def get_queryset(self):
        qs=super().get_queryset();return qs if has_perm(self.request.user,'online_ordering.manage') else qs.none()
    def perform_create(self,serializer):
        if not has_perm(self.request.user,'online_ordering.manage'):raise PermissionDenied('دسترسی ندارید')
        super().perform_create(serializer)

class TableQrTokenVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=TableQrTokenSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=TableQrToken.objects.select_related('table__hall__branch').all()
        if not has_perm(self.request.user,'online_ordering.manage'):
            return qs.none()
        return scope_queryset(
            qs,self.request.user,
            branch_path='table__hall__branch',business_path='table__hall__branch__business'
        )

    @action(detail=True,methods=['post'])
    def regenerate(self,request,pk=None):
        import uuid
        if not has_perm(request.user,'online_ordering.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        x=self.get_object()
        x.token=uuid.uuid4()
        x.save(update_fields=['token','updated_at'])
        return Response(self.get_serializer(x).data)

class OnlineOrderVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=OnlineOrderSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=OnlineOrder.objects.select_related('branch','order').all()
        if not has_perm(self.request.user,'online_ordering.manage'):
            return qs.none()
        return scope_queryset(qs,self.request.user,branch_path='branch',business_path='branch__business')

    @action(detail=True,methods=['post'])
    def accept(self,request,pk=None):
        if not has_perm(request.user,'online_ordering.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        x=self.get_object()
        x.status=OnlineOrder.Status.ACCEPTED
        x.save(update_fields=['status','updated_at'])
        return Response(self.get_serializer(x).data)

    @action(detail=True,methods=['post'])
    def reject(self,request,pk=None):
        if not has_perm(request.user,'online_ordering.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        x=self.get_object()
        if x.order.status==Order.Status.DRAFT:
            x.order.status=Order.Status.CANCELLED
            x.order.save(update_fields=['status','updated_at'])
            x.order.payments.filter(status=Payment.Status.PENDING).update(status=Payment.Status.FAILED)
        elif x.order.status not in [Order.Status.CANCELLED,Order.Status.COMPLETED]:
            try:
                void_order(x.order,user=request.user,reason='رد سفارش آنلاین')
            except ValueError as e:
                return Response({'detail':str(e)},status=409)
        x.status=OnlineOrder.Status.REJECTED
        x.save(update_fields=['status','updated_at'])
        return Response(self.get_serializer(x).data)

    @action(detail=True,methods=['post'])
    def confirm_payment(self,request,pk=None):
        if not has_perm(request.user,'online_ordering.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            x=confirm_online_payment(self.get_object(),request.data.get('reference',''))
        except ValueError as e:
            return Response({'detail':str(e)},status=409)
        return Response(self.get_serializer(x).data)

class BillSplitVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=BillSplitSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=BillSplit.objects.prefetch_related('lines__order_item','payments').select_related('order__branch').all()
        if not has_perm(self.request.user,'payments.split'):
            return qs.none()
        return scope_queryset(
            qs,self.request.user,
            branch_path='order__branch',business_path='order__branch__business'
        )

    @action(detail=True,methods=['post'])
    def settle(self,request,pk=None):
        if not has_perm(request.user,'payments.split'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            rows=settle_bill_split(self.get_object(),payments=request.data.get('payments',[]),user=request.user)
        except ValueError as e:
            return Response({'detail':str(e)},status=400)
        return Response(PaymentSerializer(rows,many=True).data,status=201)

