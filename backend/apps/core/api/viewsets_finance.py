from .shared import *
from .shared import BaseVS, _branch_accessible

class CashRegisterVS(BaseVS):
    cafino_read_permission=('cashier.use', 'cashier.view', 'settings.manage')
    cafino_write_permission='settings.manage'
    queryset=CashRegister.objects.all()
    serializer_class=CashRegisterSerializer

class CashShiftVS(BaseVS):
    cafino_read_permission=('cashier.use', 'cashier.view')
    cafino_write_permission='cashier.use'
    queryset=CashShift.objects.select_related('register__branch','cashier').all()
    serializer_class=CashShiftSerializer

    def perform_create(self,serializer):
        self._assert_write_permission()
        self._assert_write_scope(serializer.validated_data)
        register=serializer.validated_data['register']
        assert_branch_access(self.request.user,register.branch)
        if CashShift.objects.filter(register=register,is_open=True).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError('برای این صندوق یک شیفت باز وجود دارد')
        serializer.save(cashier=self.request.user)

    @action(detail=True,methods=["post"])
    def close(self,request,pk=None):
        if not has_perm(request.user,'cashier.use'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            shift=close_shift(self.get_object(),request.data.get("actual_cash",0))
        except ValueError as e:
            return Response({"detail":str(e)},status=409)
        return Response(self.get_serializer(shift).data)

class CashMovementVS(BaseVS): queryset=CashMovement.objects.all(); serializer_class=CashMovementSerializer; filterset_fields=["shift","movement_type"]; cafino_read_permission=('cashier.use', 'cashier.view')

class SupplierVS(BaseVS): queryset=Supplier.objects.all(); serializer_class=SupplierSerializer; cafino_write_permission='purchasing.manage'; search_fields=["name","phone"]; cafino_read_permission=('suppliers.view', 'purchasing.view', 'purchasing.manage')

class PurchaseInvoiceVS(BaseVS):
    cafino_read_permission=('purchasing.view', 'purchasing.manage')
    queryset=PurchaseInvoice.objects.select_related("branch","supplier").prefetch_related(
        "items__inventory_item"
    ).all()
    serializer_class=PurchaseInvoiceSerializer

    @action(detail=True,methods=["post"])
    def post_invoice(self,request,pk=None):
        if not has_perm(request.user,'purchasing.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            obj=post_purchase(self.get_object())
        except ValueError as e:
            return Response({"detail":str(e)},status=409)
        return Response(self.get_serializer(obj).data)

    @action(detail=True,methods=["post"])
    def pay(self,request,pk=None):
        if not has_perm(request.user,'purchasing.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            payment=pay_supplier(
                invoice=self.get_object(),amount=request.data.get('amount'),
                method=request.data.get('method','CASH'),reference=request.data.get('reference',''),
                user=request.user
            )
        except ValueError as e:
            return Response({"detail":str(e)},status=400)
        return Response(SupplierPaymentSerializer(payment).data,status=201)

class PurchaseItemVS(BaseVS):
    queryset=PurchaseItem.objects.all()
    serializer_class=PurchaseItemSerializer
    cafino_read_permission=('purchasing.view', 'purchasing.manage')

    def create(self,request,*args,**kwargs):
        return Response({'detail':'ثبت مستقیم آیتم خرید مجاز نیست؛ از فرآیند خرید استفاده کنید.'},status=403)

    def update(self,request,*args,**kwargs):
        return Response({'detail':'ویرایش مستقیم آیتم خرید مجاز نیست.'},status=403)

    def partial_update(self,request,*args,**kwargs):
        return Response({'detail':'ویرایش مستقیم آیتم خرید مجاز نیست.'},status=403)

class SupplierPaymentVS(BaseVS): queryset=SupplierPayment.objects.all(); serializer_class=SupplierPaymentSerializer; cafino_read_permission=('purchasing.view', 'purchasing.manage')

class ExpenseCategoryVS(BaseVS): queryset=ExpenseCategory.objects.all(); serializer_class=ExpenseCategorySerializer; cafino_write_permission='expenses.manage'; cafino_read_permission=('expenses.manage', 'reports.view')

class BankAccountVS(BaseVS):
    queryset=BankAccount.objects.select_related('branch').all()
    serializer_class=BankAccountSerializer
    cafino_read_permission=('orders.create', 'cashier.use', 'settings.manage')
    cafino_write_permission='settings.manage'
    filterset_fields=['branch', 'kind', 'is_active']

class ExpenseVS(BaseVS):
    cafino_read_permission=('expenses.manage', 'reports.view')
    cafino_write_permission='expenses.manage'
    queryset=Expense.objects.select_related('branch','category').all()
    serializer_class=ExpenseSerializer
    filterset_fields=["branch","category"]

    def create(self,request,*args,**kwargs):
        if not has_perm(request.user,'expenses.manage'):
            return Response({'detail':'دسترسی ندارید'},status=403)
        try:
            branch=resolve_branch_for_user(request.user,request.data.get('branch'))
        except Exception:
            return Response({'detail':'شعبه هزینه معتبر نیست'},status=403)
        category=None
        if request.data.get('category'):
            category=get_object_or_404(ExpenseCategory,pk=request.data.get('category'))
            if category.branch_id!=branch.id:
                return Response({'detail':'دسته هزینه متعلق به شعبه نیست'},status=400)
        bank_account=None
        if request.data.get('bank_account'):
            bank_account=get_object_or_404(BankAccount,pk=request.data.get('bank_account'))
        try:
            expense=create_expense(
                branch=branch,title=request.data.get('title','هزینه'),amount=request.data.get('amount'),
                occurred_at=request.data.get('occurred_at'),category=category,
                bank_account=bank_account,
                payment_method=request.data.get('payment_method','CASH'),
                notes=request.data.get('notes',''),user=request.user
            )
        except ValueError as ex:
            return Response({'detail':str(ex)},status=400)
        return Response(self.get_serializer(expense).data,status=201)

class FixedOverheadVS(BaseVS): queryset=FixedOverhead.objects.all(); serializer_class=FixedOverheadSerializer; cafino_write_permission='expenses.manage'; filterset_fields=["branch","is_active"]; cafino_read_permission=('expenses.manage', 'reports.view')

class DailyClosingVS(viewsets.ReadOnlyModelViewSet):
    serializer_class=DailyClosingSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=DailyClosing.objects.select_related('branch','closed_by').all()
        if not (has_perm(self.request.user,'reports.view') or has_perm(self.request.user,'daily_close.execute')):
            return qs.none()
        return scope_queryset(qs,self.request.user,branch_path='branch',business_path='branch__business')

class FiscalSettingsVS(BaseVS):
    cafino_read_permission='fiscal.manage'
    cafino_write_permission='fiscal.manage'
    queryset=FiscalSettings.objects.select_related('branch__business').all()
    serializer_class=FiscalSettingsSerializer

    def get_queryset(self):
        qs=super().get_queryset()
        return qs if has_perm(self.request.user,'fiscal.manage') else qs.none()

class GiftCardVS(viewsets.ReadOnlyModelViewSet):
    queryset=GiftCard.objects.prefetch_related('transactions').select_related('branch').all()
    serializer_class=GiftCardSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=super().get_queryset()
        if not has_perm(self.request.user,'giftcards.manage'):
            return qs.none()
        return scope_queryset(qs,self.request.user,branch_path='branch',business_path='branch__business')

class PaymentGatewayConfigVS(BaseVS):
    cafino_read_permission='payment_gateway.manage'
    cafino_write_permission='payment_gateway.manage'
    queryset=PaymentGatewayConfig.objects.select_related('branch').all();serializer_class=PaymentGatewayConfigSerializer
    def get_queryset(self):
        qs=super().get_queryset()
        return qs if has_perm(self.request.user,'payment_gateway.manage') else qs.none()
    def perform_create(self,serializer):
        if not has_perm(self.request.user,'payment_gateway.manage'):raise PermissionDenied('دسترسی ندارید')
        super().perform_create(serializer)

class GatewayIntentVS(viewsets.ReadOnlyModelViewSet):
    queryset=GatewayIntent.objects.select_related('payment__order__branch').all()
    serializer_class=GatewayIntentSerializer
    permission_classes=[permissions.IsAuthenticated]

    def get_queryset(self):
        qs=super().get_queryset()
        if not has_perm(self.request.user,'payment_gateway.manage'):
            return qs.none()
        return scope_queryset(
            qs,self.request.user,
            branch_path='payment__order__branch',business_path='payment__order__branch__business'
        )
