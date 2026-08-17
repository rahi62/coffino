from .shared import *
from .shared import BaseVS, _branch_accessible

class AuditLogVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=AuditLogSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=AuditLog.objects.select_related('actor','business','branch').all()
        if not has_perm(self.request.user,'audit.view'):
            return qs.none()
        if self.request.user.is_superuser:
            return qs
        business=tenant_business(self.request.user)
        if business is None:
            return qs.none()
        if self.request.user.branch_id and not has_perm(self.request.user,'branches.dashboard'):
            return qs.filter(models.Q(branch=self.request.user.branch)|models.Q(business=business,branch__isnull=True))
        return qs.filter(models.Q(business=business)|models.Q(business__isnull=True,branch__business=business)).distinct()

class ApprovalRequestVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=ApprovalRequestSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=ApprovalRequest.objects.select_related('order__branch','requested_by','approved_by').all()
        if has_perm(self.request.user,'approvals.decide'):
            return scope_queryset(qs,self.request.user,branch_path='order__branch',business_path='order__branch__business')
        return scope_queryset(
            qs.filter(requested_by=self.request.user),self.request.user,
            branch_path='order__branch',business_path='order__branch__business'
        )

    @action(detail=True,methods=['post'])
    def approve(self,request,pk=None):
        if not has_perm(request.user,'approvals.decide'):
            return Response({'detail':'اجازه تأیید ندارید'},status=403)
        a=self.get_object()
        if a.status!=ApprovalRequest.Status.PENDING:
            return Response({'detail':'درخواست قبلاً بررسی شده'},status=409)
        if a.request_type==ApprovalRequest.Type.DISCOUNT:
            if a.order.payment_status!=Order.PaymentStatus.UNPAID:
                return Response({'detail':'تخفیف این سفارش دیگر قابل اعمال نیست؛ سفارش پرداخت شده است'},status=409)
            apply_discount(a.order,amount=a.amount,percent=a.percent,user=request.user,reason=a.reason)
        else:
            void_order(a.order,user=request.user,reason=a.reason)
        a.status=ApprovalRequest.Status.APPROVED
        a.approved_by=request.user
        a.decided_at=timezone.now()
        a.save(update_fields=['status','approved_by','decided_at','updated_at'])
        log_action(actor=request.user,branch=a.order.branch,action='APPROVAL_APPROVED',entity=a,description=a.reason,request=request)
        return Response(self.get_serializer(a).data)

    @action(detail=True,methods=['post'])
    def reject(self,request,pk=None):
        if not has_perm(request.user,'approvals.decide'):
            return Response({'detail':'اجازه رد ندارید'},status=403)
        a=self.get_object()
        if a.status!=ApprovalRequest.Status.PENDING:
            return Response({'detail':'درخواست قبلاً بررسی شده'},status=409)
        a.status=ApprovalRequest.Status.REJECTED
        a.approved_by=request.user
        a.decided_at=timezone.now()
        a.save(update_fields=['status','approved_by','decided_at','updated_at'])
        log_action(actor=request.user,branch=a.order.branch,action='APPROVAL_REJECTED',entity=a,description=request.data.get('reason',''),request=request)
        return Response(self.get_serializer(a).data)

class UserManagementVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=UserManagementSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=User.objects.select_related('business','branch','branch__business').all()
        if self.request.user.is_superuser:
            return qs
        business=tenant_business(self.request.user)
        if business is None:
            return qs.none()
        if has_perm(self.request.user,'permissions.manage'):
            scoped=qs.filter(business=business)
            if self.request.user.role!=User.Role.OWNER:
                scoped=scoped.exclude(role=User.Role.OWNER)
            return scoped
        return qs.filter(pk=self.request.user.pk)

    @action(detail=True,methods=['post'])
    def permissions(self,request,pk=None):
        if not has_perm(request.user,'permissions.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        u=self.get_object()
        if not request.user.is_superuser and request.user.role!=User.Role.OWNER and u.role==User.Role.OWNER:
            return Response({'detail':'فقط مالک می‌تواند دسترسی‌های مالک را تغییر دهد'},status=403)
        overrides=request.data.get('overrides',{})
        clean={k:bool(v) for k,v in overrides.items() if k in ALL_PERMISSION_CODES}
        u.permission_overrides=clean
        u.save(update_fields=['permission_overrides'])
        log_action(actor=request.user,branch=u.branch,action='PERMISSIONS_UPDATED',entity=u,after={'overrides':clean},request=request)
        return Response(self.get_serializer(u).data)

    @action(detail=True,methods=['post'])
    def role(self,request,pk=None):
        if not has_perm(request.user,'permissions.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        u=self.get_object()
        role=request.data.get('role')
        if role not in dict(User.Role.choices):
            return Response({'detail':'نقش نامعتبر'},status=400)
        if not request.user.is_superuser and request.user.role!=User.Role.OWNER:
            if u.role==User.Role.OWNER or role==User.Role.OWNER:
                return Response({'detail':'فقط مالک می‌تواند نقش مالک را مدیریت کند'},status=403)
        branch_supplied='branch' in request.data
        branch_id=request.data.get('branch')
        business_id=request.data.get('business')
        if business_id is not None:
            business=get_object_or_404(Business,pk=business_id)
            assert_business_access(request.user,business)
            u.business=business
        if branch_supplied:
            if branch_id:
                branch=get_object_or_404(Branch.objects.select_related('business'),pk=branch_id)
                assert_branch_access(request.user,branch)
                u.branch=branch
                u.business=branch.business
            elif role in User.OPERATIONAL_ROLES:
                return Response({'detail':'نقش عملیاتی باید شعبه مشخص داشته باشد'},status=400)
            else:
                u.branch=None
        elif role in User.OPERATIONAL_ROLES and not u.branch_id:
            return Response({'detail':'نقش عملیاتی باید شعبه مشخص داشته باشد'},status=400)
        before={'role':u.role,'branch':u.branch_id,'business':u.business_id}
        u.role=role
        try:
            u.save()
        except Exception as e:
            return Response({'detail':'ترکیب نقش، کسب‌وکار و شعبه معتبر نیست'},status=400)
        log_action(
            actor=request.user,branch=u.branch,action='ROLE_UPDATED',entity=u,before=before,
            after={'role':u.role,'branch':u.branch_id,'business':u.business_id},request=request
        )
        return Response(self.get_serializer(u).data)

class DiscountRuleVS(BaseVS):
    cafino_read_permission='discount.rules.manage'
    cafino_write_permission='discount.rules.manage'
    queryset=DiscountRule.objects.select_related('branch','category','product').all()
    serializer_class=DiscountRuleSerializer

    def get_queryset(self):
        qs=super().get_queryset()
        return qs if has_perm(self.request.user,'discount.rules.manage') else qs.none()

    def perform_create(self,serializer):
        super().perform_create(serializer)

    def perform_update(self,serializer):
        super().perform_update(serializer)

    def perform_destroy(self,instance):
        self._assert_write_permission()
        instance.delete()

class StaffScheduleVS(BaseVS):
    cafino_read_permission=('workforce.manage', 'workforce.clock')
    cafino_write_permission='workforce.manage'
    queryset=StaffSchedule.objects.select_related('user__business','user__branch','branch').all()
    serializer_class=StaffScheduleSerializer

    def get_queryset(self):
        qs=super().get_queryset()
        if not has_perm(self.request.user,'workforce.manage'):
            qs=qs.filter(user=self.request.user)
        return qs

    def perform_create(self,serializer):
        super().perform_create(serializer)

    def perform_update(self,serializer):
        super().perform_update(serializer)

    def perform_destroy(self,instance):
        self._assert_write_permission()
        instance.delete()

class AttendanceVS(viewsets.ReadOnlyModelViewSet):
    queryset=Attendance.objects.select_related('user','branch').all()
    serializer_class=AttendanceSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=scope_queryset(
            super().get_queryset(),self.request.user,
            branch_path='branch',business_path='branch__business'
        )
        if not has_perm(self.request.user,'workforce.manage'):
            qs=qs.filter(user=self.request.user)
        return qs

class PrinterDeviceVS(BaseVS):
    cafino_read_permission=('printing.manage', 'printing.use')
    cafino_write_permission='printing.manage'
    queryset=PrinterDevice.objects.select_related('branch__business').all()
    serializer_class=PrinterDeviceSerializer

    def get_queryset(self):
        qs=super().get_queryset()
        return qs if has_perm(self.request.user,'printing.manage') else qs.none()

class PrintTemplateVS(BaseVS):
    cafino_read_permission=('printing.manage', 'printing.use')
    cafino_write_permission='printing.manage'
    queryset=PrintTemplate.objects.all();serializer_class=PrintTemplateSerializer
    def perform_create(self,serializer):
        if not has_perm(self.request.user,'printing.manage'):raise PermissionDenied('دسترسی ندارید')
        super().perform_create(serializer)
    def perform_update(self,serializer):
        if not has_perm(self.request.user,'printing.manage'):raise PermissionDenied('دسترسی ندارید')
        super().perform_update(serializer)

class PrintJobVS(viewsets.ReadOnlyModelViewSet):
    queryset=PrintJob.objects.select_related('printer','branch').all()
    serializer_class=PrintJobSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=super().get_queryset()
        if not (has_perm(self.request.user,'printing.use') or has_perm(self.request.user,'printing.manage')):
            return qs.none()
        return scope_queryset(qs,self.request.user,branch_path='branch',business_path='branch__business')

    @action(detail=True,methods=['post'])
    def mark_printed(self,request,pk=None):
        if not has_perm(request.user,'printing.use'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        j=self.get_object()
        j.status=PrintJob.Status.PRINTED
        j.printed_at=timezone.now()
        j.error=''
        j.save(update_fields=['status','printed_at','error','updated_at'])
        return Response(self.get_serializer(j).data)

    @action(detail=True,methods=['post'])
    def mark_failed(self,request,pk=None):
        if not has_perm(request.user,'printing.use'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        j=self.get_object()
        j.status=PrintJob.Status.FAILED
        j.error=(request.data.get('error') or 'Print failed')[:1000]
        j.save(update_fields=['status','error','updated_at'])
        return Response(self.get_serializer(j).data)

class LoyaltyProgramVS(BaseVS):
    cafino_read_permission='loyalty.manage'
    cafino_write_permission='loyalty.manage'
    queryset=LoyaltyProgram.objects.select_related('branch').all();serializer_class=LoyaltyProgramSerializer
    def get_queryset(self):
        qs=super().get_queryset();return qs if has_perm(self.request.user,'loyalty.manage') else qs.none()
    def perform_create(self,serializer):
        if not has_perm(self.request.user,'loyalty.manage'):raise PermissionDenied('دسترسی ندارید')
        super().perform_create(serializer)

class CustomerLoyaltyAccountVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=CustomerLoyaltyAccountSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=CustomerLoyaltyAccount.objects.select_related('customer__branch').all()
        if not has_perm(self.request.user,'loyalty.manage'):
            return qs.none()
        return scope_queryset(
            qs,self.request.user,
            branch_path='customer__branch',business_path='customer__branch__business'
        )

class WalletAccountVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=WalletAccountSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=WalletAccount.objects.select_related('customer__branch').all()
        if not has_perm(self.request.user,'loyalty.manage'):
            return qs.none()
        return scope_queryset(
            qs,self.request.user,
            branch_path='customer__branch',business_path='customer__branch__business'
        )

class NotificationVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=NotificationSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=Notification.objects.select_related('branch','order','customer').all()
        if not has_perm(self.request.user,'notifications.manage'):
            return qs.none()
        return scope_queryset(qs,self.request.user,branch_path='branch',business_path='branch__business')

    @action(detail=True,methods=['post'])
    def retry(self,request,pk=None):
        if not has_perm(request.user,'notifications.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        x=self.get_object()
        x.status=Notification.Status.PENDING
        x.next_attempt_at=None
        x.save(update_fields=['status','next_attempt_at','updated_at'])
        return Response(self.get_serializer(process_notification(x)).data)

class SmsProviderConfigVS(BaseVS):
    cafino_read_permission='notifications.manage'
    cafino_write_permission='notifications.manage'
    queryset=SmsProviderConfig.objects.select_related('branch').all()
    serializer_class=SmsProviderConfigSerializer

    def get_queryset(self):
        qs=super().get_queryset()
        return qs if has_perm(self.request.user,'notifications.manage') else qs.none()

    def perform_create(self,serializer):
        super().perform_create(serializer)

class DeliveryZoneVS(BaseVS):
    cafino_read_permission='delivery.manage'
    cafino_write_permission='delivery.manage'
    queryset=DeliveryZone.objects.select_related('branch').all();serializer_class=DeliveryZoneSerializer
    def get_queryset(self):
        qs=super().get_queryset()
        return qs if has_perm(self.request.user,'delivery.manage') else qs.none()
    def perform_create(self,serializer):
        if not has_perm(self.request.user,'delivery.manage'):raise PermissionDenied('دسترسی ندارید')
        super().perform_create(serializer)

class DeliveryAddressVS(BaseVS):
    cafino_read_permission='delivery.manage'
    cafino_write_permission='delivery.manage'
    queryset=DeliveryAddress.objects.select_related('branch','zone','customer').all();serializer_class=DeliveryAddressSerializer
    def perform_create(self,serializer):
        if not has_perm(self.request.user,'delivery.manage'):raise PermissionDenied('دسترسی ندارید')
        super().perform_create(serializer)

class CourierProfileVS(BaseVS):
    cafino_read_permission='delivery.manage'
    cafino_write_permission='delivery.manage'
    queryset=CourierProfile.objects.select_related('branch','user').all();serializer_class=CourierProfileSerializer
    def get_queryset(self):
        qs=super().get_queryset()
        return qs if has_perm(self.request.user,'delivery.manage') else qs.none()
    def perform_create(self,serializer):
        if not has_perm(self.request.user,'delivery.manage'):raise PermissionDenied('دسترسی ندارید')
        super().perform_create(serializer)
    def perform_update(self,serializer):
        if not has_perm(self.request.user,'delivery.manage'):raise PermissionDenied('دسترسی ندارید')
        super().perform_update(serializer)

class DeliveryAssignmentVS(viewsets.ReadOnlyModelViewSet):
    queryset=DeliveryAssignment.objects.select_related('order__branch','address','zone','courier').all()
    serializer_class=DeliveryAssignmentSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=super().get_queryset()
        if not has_perm(self.request.user,'delivery.manage'):
            return qs.none()
        return scope_queryset(
            qs,self.request.user,
            branch_path='order__branch',business_path='order__branch__business'
        )

    @action(detail=True,methods=['post'])
    def assign(self,request,pk=None):
        courier=get_object_or_404(CourierProfile.objects.select_related('branch'),pk=request.data.get('courier'))
        assignment=self.get_object()
        if courier.branch_id!=assignment.order.branch_id:
            return Response({'detail':'پیک متعلق به شعبه سفارش نیست'},status=400)
        try:
            x=assign_courier(assignment,courier,user=request.user)
        except ValueError as e:
            return Response({'detail':str(e)},status=409)
        return Response(self.get_serializer(x).data)

    @action(detail=True,methods=['post'])
    def status_update(self,request,pk=None):
        if not has_perm(request.user,'delivery.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            x=update_delivery_status(
                self.get_object(),request.data.get('status'),user=request.user,note=request.data.get('note','')
            )
        except ValueError as e:
            return Response({'detail':str(e)},status=409)
        return Response(self.get_serializer(x).data)

class LoyaltyTierVS(BaseVS):
    cafino_read_permission='loyalty.manage'
    cafino_write_permission='loyalty.manage'
    queryset=LoyaltyTier.objects.all();serializer_class=LoyaltyTierSerializer
    def get_queryset(self):
        qs=super().get_queryset();return qs if has_perm(self.request.user,'loyalty.manage') else qs.none()
    def perform_create(self,serializer):
        if not has_perm(self.request.user,'loyalty.manage'):raise PermissionDenied('دسترسی ندارید')
        super().perform_create(serializer)

class LoyaltyCampaignVS(BaseVS):
    cafino_read_permission='loyalty.manage'
    cafino_write_permission='loyalty.manage'
    queryset=LoyaltyCampaign.objects.all();serializer_class=LoyaltyCampaignSerializer
    def get_queryset(self):
        qs=super().get_queryset();return qs if has_perm(self.request.user,'loyalty.manage') else qs.none()
    def perform_create(self,serializer):
        if not has_perm(self.request.user,'loyalty.manage'):raise PermissionDenied('دسترسی ندارید')
        super().perform_create(serializer)

class PushProviderConfigVS(BaseVS):
    cafino_read_permission='notifications.manage'
    cafino_write_permission='notifications.manage'
    queryset=PushProviderConfig.objects.all();serializer_class=PushProviderConfigSerializer
    def get_queryset(self):
        qs=super().get_queryset();return qs if has_perm(self.request.user,'notifications.manage') else qs.none()
    def perform_create(self,serializer):
        if not has_perm(self.request.user,'notifications.manage'):raise PermissionDenied('دسترسی ندارید')
        super().perform_create(serializer)

