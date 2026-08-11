from decimal import Decimal
from rest_framework import serializers
from apps.businesses.models import Business, Branch, BusinessModule
from apps.catalog.models import Category, Product
from apps.customers.models import Customer
from apps.dining.models import Hall, Table, TableSession
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment, Refund
from apps.kitchen.models import PreparationStation, KitchenTicket
from apps.inventory.models import IngredientCategory, InventoryItem, StockMovement, RecipeItem
from apps.takeaway.models import PagerDevice, TakeawayProfile
from apps.cashier.models import CashRegister, CashShift, CashMovement
from apps.suppliers.models import Supplier
from apps.purchasing.models import PurchaseInvoice, PurchaseItem, SupplierPayment
from apps.accounting.models import BankAccount, ExpenseCategory, Expense, FixedOverhead

class BusinessSerializer(serializers.ModelSerializer):
    class Meta: model=Business; fields="__all__"
class BranchSerializer(serializers.ModelSerializer):
    class Meta: model=Branch; fields="__all__"
class BusinessModuleSerializer(serializers.ModelSerializer):
    class Meta: model=BusinessModule; fields="__all__"
class CategorySerializer(serializers.ModelSerializer):
    def validate_name(self,value):
        value=value.strip()
        if not value:
            raise serializers.ValidationError('نام دسته‌بندی را وارد کنید.')
        return value

    def validate(self,attrs):
        branch=attrs.get('branch',getattr(self.instance,'branch',None))
        name=attrs.get('name',getattr(self.instance,'name',''))
        if branch and name:
            existing=Category.objects.filter(branch=branch,name__iexact=name)
            if self.instance:
                existing=existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError({'name':'دسته‌بندی با این نام در شعبهٔ انتخاب‌شده وجود دارد.'})
        return attrs

    class Meta: model=Category; fields="__all__"
class ProductSerializer(serializers.ModelSerializer):
    category_name=serializers.CharField(source="category.name",read_only=True)
    station_name=serializers.CharField(source="preparation_station.name",read_only=True)
    def validate(self,attrs):
        branch=attrs.get('branch',getattr(self.instance,'branch',None));category=attrs.get('category',getattr(self.instance,'category',None));station=attrs.get('preparation_station',getattr(self.instance,'preparation_station',None));stock=attrs.get('stock_item',getattr(self.instance,'stock_item',None))
        if branch and category and category.branch_id!=branch.id:raise serializers.ValidationError('دسته متعلق به شعبه محصول نیست')
        if branch and station and station.branch_id!=branch.id:raise serializers.ValidationError('ایستگاه آماده‌سازی متعلق به شعبه محصول نیست')
        if branch and stock and stock.branch_id!=branch.id:raise serializers.ValidationError('Finished Good متعلق به شعبه محصول نیست')
        return attrs
    class Meta: model=Product; fields="__all__" 
class CustomerSerializer(serializers.ModelSerializer):
    class Meta: model=Customer; fields="__all__"
class HallSerializer(serializers.ModelSerializer):
    class Meta: model=Hall; fields="__all__"
class TableSerializer(serializers.ModelSerializer):
    hall_name=serializers.CharField(source="hall.name",read_only=True)
    class Meta: model=Table; fields="__all__"
class TableSessionSerializer(serializers.ModelSerializer):
    table_number=serializers.CharField(source="table.number",read_only=True)
    class Meta: model=TableSession; fields="__all__"
class OrderItemSerializer(serializers.ModelSerializer):
    station_name=serializers.CharField(source="product.preparation_station.name",read_only=True,allow_null=True)
    class Meta: model=OrderItem; fields="__all__"
class RefundSerializer(serializers.ModelSerializer):
    class Meta: model=Refund; fields="__all__"
class PaymentSerializer(serializers.ModelSerializer):
    refunds=RefundSerializer(many=True,read_only=True)
    refunded_amount=serializers.SerializerMethodField()
    bank_account_name=serializers.CharField(source='bank_account.display_name',read_only=True,allow_null=True)
    def get_refunded_amount(self,obj): return sum((x.amount for x in obj.refunds.all()),0)
    class Meta:
        model=Payment; fields="__all__"
        read_only_fields=['order','amount','method','status','reference_number','payer_label','tendered_amount','change_amount','received_by']
class TakeawayProfileSerializer(serializers.ModelSerializer):
    pager_number=serializers.CharField(source="pager.number",read_only=True,allow_null=True)
    class Meta: model=TakeawayProfile; fields="__all__"
class OrderSerializer(serializers.ModelSerializer):
    items=OrderItemSerializer(many=True,read_only=True)
    payments=PaymentSerializer(many=True,read_only=True)
    table_number=serializers.SerializerMethodField()
    takeaway=serializers.SerializerMethodField()
    kitchen_statuses=serializers.SerializerMethodField()
    outstanding_amount=serializers.SerializerMethodField()
    def get_table_number(self,obj):
        return obj.table_session.table.number if obj.table_session_id else None
    def get_takeaway(self,obj):
        try:return TakeawayProfileSerializer(obj.takeaway_profile).data
        except TakeawayProfile.DoesNotExist:return None
    def get_kitchen_statuses(self,obj):
        return [
            {'station_id':ticket.station_id,'station_name':ticket.station.name,'status':ticket.status}
            for ticket in obj.kitchen_tickets.all()
        ]
    def get_outstanding_amount(self,obj):
        settled_statuses={Payment.Status.SUCCEEDED,Payment.Status.PARTIALLY_REFUNDED,Payment.Status.REFUNDED}
        paid=sum((payment.amount for payment in obj.payments.all() if payment.status in settled_statuses),Decimal('0'))
        return str(max(Decimal('0'),Decimal(obj.grand_total)-paid))
    class Meta:
        model=Order; fields="__all__"
        read_only_fields=['subtotal','discount_total','discount_rule','discount_reason','tax_total','service_charge_total','delivery_fee_total','grand_total','payment_status','idempotency_key','idempotency_fingerprint','created_by']
class PreparationStationSerializer(serializers.ModelSerializer):
    class Meta: model=PreparationStation; fields="__all__"
class KitchenTicketSerializer(serializers.ModelSerializer):
    order_number=serializers.IntegerField(source="order.order_number",read_only=True)
    order_type=serializers.CharField(source="order.order_type",read_only=True)
    order_status=serializers.CharField(source="order.status",read_only=True)
    payment_status=serializers.CharField(source="order.payment_status",read_only=True)
    station_name=serializers.CharField(source="station.name",read_only=True)
    items=serializers.SerializerMethodField()
    fulfillment_destination=serializers.SerializerMethodField()
    ready_notification_method=serializers.SerializerMethodField()
    ready_notification_status=serializers.SerializerMethodField()
    def get_items(self,obj):
        qs=obj.order.items.filter(product__preparation_station=obj.station)
        return OrderItemSerializer(qs,many=True).data
    def get_fulfillment_destination(self,obj):
        order=obj.order
        if order.order_type==Order.Type.DINE_IN:
            return f'میز {order.table_session.table.number}' if order.table_session_id else 'داخل سالن'
        if order.order_type==Order.Type.TAKEAWAY:
            try:
                profile=order.takeaway_profile
                if profile.ready_notification_method=='PAGER':
                    return f'پیجر {profile.pager.number}' if profile.pager_id else 'پیجر انتخاب نشده'
                if profile.ready_notification_method=='SMS':
                    return 'پیامک به مشتری' if profile.customer_phone else 'شماره همراه ثبت نشده'
            except TakeawayProfile.DoesNotExist:
                pass
            return 'بیرون‌بر'
        return dict(Order.Type.choices).get(order.order_type,order.order_type)
    def get_ready_notification_method(self,obj):
        try:return obj.order.takeaway_profile.ready_notification_method
        except TakeawayProfile.DoesNotExist:return None
    def get_ready_notification_status(self,obj):
        if obj.order.order_type!=Order.Type.TAKEAWAY:return None
        from apps.notifications.models import Notification
        return Notification.objects.filter(order=obj.order,event='ORDER_READY').exclude(channel=Notification.Channel.IN_APP).values_list('status',flat=True).first()
    class Meta: model=KitchenTicket; fields="__all__"
class IngredientCategorySerializer(serializers.ModelSerializer):
    def validate_name(self,value):
        value=value.strip()
        if not value:raise serializers.ValidationError('نام دستهٔ مواد اولیه را وارد کنید.')
        return value
    def validate(self,attrs):
        branch=attrs.get('branch',getattr(self.instance,'branch',None));name=attrs.get('name',getattr(self.instance,'name',''))
        if branch and name:
            exists=IngredientCategory.objects.filter(branch=branch,name__iexact=name)
            if self.instance:exists=exists.exclude(pk=self.instance.pk)
            if exists.exists():raise serializers.ValidationError({'name':'دسته‌ای با این نام در شعبهٔ انتخاب‌شده وجود دارد.'})
        return attrs
    class Meta:model=IngredientCategory;fields='__all__'

class InventoryItemSerializer(serializers.ModelSerializer):
    material_category_name=serializers.CharField(source='material_category.name',read_only=True,allow_null=True)
    low_stock=serializers.SerializerMethodField()
    usable_stock=serializers.SerializerMethodField()
    expired_stock=serializers.SerializerMethodField()
    blocked_stock=serializers.SerializerMethodField()
    def get_low_stock(self,obj): return obj.current_stock <= obj.minimum_stock
    def get_usable_stock(self,obj):
        if not obj.lot_tracked:return obj.current_stock
        from django.utils import timezone
        from django.db.models import Sum,Q
        return obj.lots.filter(is_blocked=False,quantity_remaining__gt=0).filter(Q(expires_at__isnull=True)|Q(expires_at__gt=timezone.now())).aggregate(v=Sum('quantity_remaining'))['v'] or 0
    def get_expired_stock(self,obj):
        if not obj.lot_tracked:return 0
        from django.utils import timezone
        from django.db.models import Sum
        return obj.lots.filter(expires_at__lte=timezone.now(),quantity_remaining__gt=0).aggregate(v=Sum('quantity_remaining'))['v'] or 0
    def get_blocked_stock(self,obj):
        if not obj.lot_tracked:return 0
        from django.db.models import Sum
        return obj.lots.filter(is_blocked=True,quantity_remaining__gt=0).aggregate(v=Sum('quantity_remaining'))['v'] or 0
    def validate_name(self,value):
        value=value.strip()
        if not value:
            raise serializers.ValidationError('نام ماده اولیه را وارد کنید.')
        return value
    def validate(self,attrs):
        branch=attrs.get('branch',getattr(self.instance,'branch',None));name=attrs.get('name',getattr(self.instance,'name',''));material_category=attrs.get('material_category',getattr(self.instance,'material_category',None))
        if branch and material_category and material_category.branch_id!=branch.id:raise serializers.ValidationError({'material_category':'دستهٔ مواد اولیه باید متعلق به همان شعبه باشد.'})
        if branch and name:
            exists=InventoryItem.objects.filter(branch=branch,name__iexact=name)
            if self.instance:exists=exists.exclude(pk=self.instance.pk)
            if exists.exists():raise serializers.ValidationError({'name':'ماده اولیه‌ای با این نام در شعبهٔ انتخاب‌شده وجود دارد.'})
        for field in ('current_stock','minimum_stock','average_cost','last_purchase_cost'):
            value=attrs.get(field)
            if value is not None and value<0:raise serializers.ValidationError({field:'مقدار نمی‌تواند منفی باشد.'})
        return attrs
    def create(self,validated_data):
        material_category=validated_data.get('material_category')
        if material_category:validated_data['category']=material_category.name
        obj=super().create(validated_data)
        if obj.lot_tracked and obj.current_stock>0:
            from apps.inventory.models import InventoryLot
            InventoryLot.objects.create(item=obj,lot_number=f'LEGACY-{obj.id}',quantity_received=obj.current_stock,quantity_remaining=obj.current_stock,unit_cost=obj.average_cost,source_type='LOT_BOOTSTRAP',source_id=str(obj.id),notes='موجودی اولیه هنگام فعال‌سازی رهگیری سری ساخت')
        return obj
    def update(self,instance,validated_data):
        material_category=validated_data.get('material_category')
        if material_category:validated_data['category']=material_category.name
        elif 'material_category' in validated_data:validated_data['category']=''
        enabling=validated_data.get('lot_tracked',instance.lot_tracked) and not instance.lot_tracked
        disabling=(validated_data.get('lot_tracked') is False and instance.lot_tracked)
        if disabling and instance.lots.filter(quantity_remaining__gt=0).exists():raise serializers.ValidationError('تا زمانی که Lot دارای مانده است، Lot Tracking قابل غیرفعال‌سازی نیست')
        obj=super().update(instance,validated_data)
        if enabling and obj.current_stock>0 and not obj.lots.exists():
            from apps.inventory.models import InventoryLot
            InventoryLot.objects.create(item=obj,lot_number=f'LEGACY-{obj.id}',quantity_received=obj.current_stock,quantity_remaining=obj.current_stock,unit_cost=obj.average_cost,source_type='LOT_BOOTSTRAP',source_id=str(obj.id),notes='Bootstrap lot when enabling FEFO on existing stock')
        return obj
    class Meta: model=InventoryItem; fields="__all__"
class StockMovementSerializer(serializers.ModelSerializer):
    item_name=serializers.CharField(source="item.name",read_only=True)
    lot_number=serializers.CharField(source='lot.lot_number',read_only=True,allow_null=True)
    class Meta: model=StockMovement; fields="__all__"
class RecipeItemSerializer(serializers.ModelSerializer):
    inventory_name=serializers.CharField(source="inventory_item.name",read_only=True)
    product_name=serializers.CharField(source="product.name",read_only=True)
    def validate(self,attrs):
        product=attrs.get('product',getattr(self.instance,'product',None));item=attrs.get('inventory_item',getattr(self.instance,'inventory_item',None));quantity=attrs.get('quantity',getattr(self.instance,'quantity',0))
        if product and item and product.branch_id!=item.branch_id:raise serializers.ValidationError('محصول و ماده اولیه باید در یک شعبه باشند')
        if quantity is None or quantity<=0:raise serializers.ValidationError({'quantity':'مقدار ماده اولیه باید بیشتر از صفر باشد.'})
        if product and item:
            exists=RecipeItem.objects.filter(product=product,inventory_item=item)
            if self.instance:exists=exists.exclude(pk=self.instance.pk)
            if exists.exists():raise serializers.ValidationError('این ماده اولیه پیش‌تر به رسپی محصول اضافه شده است.')
        return attrs
    class Meta: model=RecipeItem; fields="__all__"


class RecipeIngredientInputSerializer(serializers.Serializer):
    """A single material line submitted by the recipe editor."""
    inventory_item=serializers.PrimaryKeyRelatedField(queryset=InventoryItem.objects.all())
    quantity=serializers.DecimalField(max_digits=14,decimal_places=3,min_value=Decimal('0.001'))


class RecipeSaveSerializer(serializers.Serializer):
    """Validate a complete recipe before it is atomically synchronised."""
    product=serializers.PrimaryKeyRelatedField(queryset=Product.objects.select_related('branch'))
    ingredients=RecipeIngredientInputSerializer(many=True,allow_empty=False)

    def validate(self,attrs):
        product=attrs['product']
        material_ids=set()
        for ingredient in attrs['ingredients']:
            item=ingredient['inventory_item']
            if item.branch_id!=product.branch_id:
                raise serializers.ValidationError('محصول و همهٔ مواد اولیه باید متعلق به یک شعبه باشند.')
            if item.id in material_ids:
                raise serializers.ValidationError({'ingredients':'هر مادهٔ اولیه فقط یک‌بار می‌تواند در رسپی باشد.'})
            material_ids.add(item.id)
        return attrs
class PagerDeviceSerializer(serializers.ModelSerializer):
    class Meta: model=PagerDevice; fields="__all__"
class CashRegisterSerializer(serializers.ModelSerializer):
    class Meta: model=CashRegister; fields="__all__"
class CashShiftSerializer(serializers.ModelSerializer):
    class Meta: model=CashShift; fields="__all__"

class CashMovementSerializer(serializers.ModelSerializer):
    class Meta: model=CashMovement; fields="__all__"
class SupplierSerializer(serializers.ModelSerializer):
    balance=serializers.SerializerMethodField()
    def get_balance(self,obj):
        from apps.purchasing.services import supplier_balance
        return supplier_balance(obj)
    class Meta: model=Supplier; fields="__all__"
class PurchaseItemSerializer(serializers.ModelSerializer):
    inventory_name=serializers.CharField(source="inventory_item.name",read_only=True)
    class Meta: model=PurchaseItem; fields="__all__"
class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    items=PurchaseItemSerializer(many=True,read_only=True)
    supplier_name=serializers.CharField(source="supplier.name",read_only=True)
    balance_due=serializers.DecimalField(max_digits=14,decimal_places=0,read_only=True)
    class Meta: model=PurchaseInvoice; fields="__all__"
class SupplierPaymentSerializer(serializers.ModelSerializer):
    bank_account_name=serializers.CharField(source='bank_account.display_name',read_only=True,allow_null=True)
    class Meta: model=SupplierPayment; fields="__all__"
class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta: model=ExpenseCategory; fields="__all__"
class BankAccountSerializer(serializers.ModelSerializer):
    display_name=serializers.CharField(read_only=True)
    class Meta: model=BankAccount; fields="__all__"
    def validate_identifier_last4(self,value):
        value=''.join(char for char in str(value or '') if char.isdigit())
        if value and len(value)!=4:
            raise serializers.ValidationError('چهار رقم پایانی را وارد کنید.')
        return value
class ExpenseSerializer(serializers.ModelSerializer):
    category_name=serializers.CharField(source="category.name",read_only=True,allow_null=True)
    bank_account_name=serializers.CharField(source="bank_account.display_name",read_only=True,allow_null=True)
    class Meta: model=Expense; fields="__all__"
class FixedOverheadSerializer(serializers.ModelSerializer):
    class Meta: model=FixedOverhead; fields="__all__"

from apps.audit.models import AuditLog
from apps.orders.models import ApprovalRequest
from apps.cashier.models import DailyClosing
class AuditLogSerializer(serializers.ModelSerializer):
    actor_name=serializers.CharField(source='actor.username',read_only=True,allow_null=True)
    class Meta: model=AuditLog; fields='__all__'
class ApprovalRequestSerializer(serializers.ModelSerializer):
    requester_name=serializers.CharField(source='requested_by.username',read_only=True)
    approver_name=serializers.CharField(source='approved_by.username',read_only=True,allow_null=True)
    order_number=serializers.IntegerField(source='order.order_number',read_only=True)
    class Meta: model=ApprovalRequest; fields='__all__'
class DailyClosingSerializer(serializers.ModelSerializer):
    closed_by_name=serializers.CharField(source='closed_by.username',read_only=True,allow_null=True)
    class Meta: model=DailyClosing; fields='__all__'

from apps.accounts.models import User
from apps.discounts.models import DiscountRule
from apps.workforce.models import StaffSchedule, Attendance
from apps.inventory.models import WasteRecord

class UserManagementSerializer(serializers.ModelSerializer):
    branch_name=serializers.CharField(source='branch.name',read_only=True,allow_null=True)
    business_name=serializers.CharField(source='business.name',read_only=True,allow_null=True)
    class Meta:
        model=User
        fields=[
            'id','username','first_name','last_name','email','role',
            'business','business_name','branch','branch_name',
            'is_active','permission_overrides'
        ]
        read_only_fields=['permission_overrides']

class DiscountRuleSerializer(serializers.ModelSerializer):
    category_name=serializers.CharField(source='category.name',read_only=True,allow_null=True)
    product_name=serializers.CharField(source='product.name',read_only=True,allow_null=True)
    class Meta:model=DiscountRule;fields='__all__'

class StaffScheduleSerializer(serializers.ModelSerializer):
    user_name=serializers.SerializerMethodField()
    def get_user_name(self,obj):return obj.user.get_full_name() or obj.user.username
    class Meta:model=StaffSchedule;fields='__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    user_name=serializers.SerializerMethodField()
    duration_minutes=serializers.SerializerMethodField()
    def get_user_name(self,obj):return obj.user.get_full_name() or obj.user.username
    def get_duration_minutes(self,obj):return obj.duration_minutes()
    class Meta:model=Attendance;fields='__all__'

class WasteRecordSerializer(serializers.ModelSerializer):
    item_name=serializers.CharField(source='item.name',read_only=True)
    created_by_name=serializers.CharField(source='created_by.username',read_only=True,allow_null=True)
    class Meta:model=WasteRecord;fields='__all__'

from apps.inventory.models import InventoryCount, InventoryCountLine, StockTransfer, StockTransferLine
from apps.production.models import ProductionFormula, ProductionFormulaItem, ProductionBatch, ProductionBatchIngredient
from apps.accounting.models import FiscalSettings
from apps.printing.models import PrinterDevice, PrintTemplate, PrintJob

class InventoryCountLineSerializer(serializers.ModelSerializer):
    item_name=serializers.CharField(source='item.name',read_only=True)
    class Meta:model=InventoryCountLine;fields='__all__'
class InventoryCountSerializer(serializers.ModelSerializer):
    lines=InventoryCountLineSerializer(many=True,read_only=True)
    counted_by_name=serializers.CharField(source='counted_by.username',read_only=True,allow_null=True)
    posted_by_name=serializers.CharField(source='posted_by.username',read_only=True,allow_null=True)
    class Meta:model=InventoryCount;fields='__all__'

class StockTransferLineSerializer(serializers.ModelSerializer):
    source_item_name=serializers.CharField(source='source_item.name',read_only=True)
    destination_item_name=serializers.CharField(source='destination_item.name',read_only=True)
    class Meta:model=StockTransferLine;fields='__all__'
class StockTransferSerializer(serializers.ModelSerializer):
    lines=StockTransferLineSerializer(many=True,read_only=True)
    source_branch_name=serializers.CharField(source='source_branch.name',read_only=True)
    destination_branch_name=serializers.CharField(source='destination_branch.name',read_only=True)
    class Meta:model=StockTransfer;fields='__all__'

class ProductionFormulaItemSerializer(serializers.ModelSerializer):
    inventory_name=serializers.CharField(source='inventory_item.name',read_only=True)
    def validate(self,attrs):
        formula=attrs.get('formula',getattr(self.instance,'formula',None));item=attrs.get('inventory_item',getattr(self.instance,'inventory_item',None));qty=attrs.get('quantity',getattr(self.instance,'quantity',0))
        if formula and item and formula.branch_id!=item.branch_id:raise serializers.ValidationError('ماده اولیه باید متعلق به شعبه فرمول باشد')
        if qty is not None and qty<=0:raise serializers.ValidationError('مقدار ماده اولیه باید مثبت باشد')
        return attrs
    class Meta:model=ProductionFormulaItem;fields='__all__'
class ProductionFormulaSerializer(serializers.ModelSerializer):
    ingredients=ProductionFormulaItemSerializer(many=True,read_only=True)
    output_item_name=serializers.CharField(source='output_item.name',read_only=True)
    def validate(self,attrs):
        branch=attrs.get('branch',getattr(self.instance,'branch',None));output=attrs.get('output_item',getattr(self.instance,'output_item',None));qty=attrs.get('output_quantity',getattr(self.instance,'output_quantity',0))
        if branch and output and branch.id!=output.branch_id:raise serializers.ValidationError('محصول خروجی باید متعلق به شعبه فرمول باشد')
        if qty is not None and qty<=0:raise serializers.ValidationError('مقدار خروجی باید مثبت باشد')
        return attrs
    class Meta:model=ProductionFormula;fields='__all__'
class ProductionBatchIngredientSerializer(serializers.ModelSerializer):
    inventory_name=serializers.CharField(source='inventory_item.name',read_only=True)
    class Meta:model=ProductionBatchIngredient;fields='__all__'
class ProductionBatchSerializer(serializers.ModelSerializer):
    formula_name=serializers.CharField(source='formula.name',read_only=True)
    ingredient_snapshots=ProductionBatchIngredientSerializer(many=True,read_only=True)
    def validate(self,attrs):
        branch=attrs.get('branch',getattr(self.instance,'branch',None));formula=attrs.get('formula',getattr(self.instance,'formula',None));mult=attrs.get('multiplier',getattr(self.instance,'multiplier',0))
        if branch and formula and branch.id!=formula.branch_id:raise serializers.ValidationError('فرمول متعلق به شعبه Batch نیست')
        if mult is not None and mult<=0:raise serializers.ValidationError('ضریب Batch باید مثبت باشد')
        return attrs
    class Meta:
        model=ProductionBatch;fields='__all__'
        read_only_fields=['produced_quantity','total_cost','unit_cost','status','created_by','posted_by','posted_at']

class FiscalSettingsSerializer(serializers.ModelSerializer):
    branch_name=serializers.CharField(source='branch.name',read_only=True)
    def validate(self,attrs):
        tax=attrs.get('tax_rate',getattr(self.instance,'tax_rate',0));service=attrs.get('service_charge_rate',getattr(self.instance,'service_charge_rate',0))
        if tax<0 or tax>100:raise serializers.ValidationError('نرخ مالیات باید بین صفر تا صد باشد')
        if service<0 or service>100:raise serializers.ValidationError('نرخ حق سرویس باید بین صفر تا صد باشد')
        return attrs
    class Meta:model=FiscalSettings;fields='__all__'

class PrinterDeviceSerializer(serializers.ModelSerializer):
    branch_name=serializers.CharField(source='branch.name',read_only=True)
    class Meta:model=PrinterDevice;fields='__all__'
class PrintTemplateSerializer(serializers.ModelSerializer):
    class Meta:model=PrintTemplate;fields='__all__'
class PrintJobSerializer(serializers.ModelSerializer):
    printer_name=serializers.CharField(source='printer.name',read_only=True,allow_null=True)
    class Meta:
        model=PrintJob;fields='__all__'
        read_only_fields=['branch','printer','document_type','entity_type','entity_id','payload','status','error','printed_at','created_by']

from apps.inventory.models import InventoryLot
from apps.reservations.models import Reservation
from apps.loyalty.models import LoyaltyProgram,CustomerLoyaltyAccount,LoyaltyLedger,WalletAccount,WalletTransaction
from apps.notifications.models import Notification,PagerProviderConfig,SmsProviderConfig
from apps.online_ordering.models import OnlineMenuSettings,TableQrToken,OnlineOrder
from apps.payments.models import BillSplit,BillSplitLine

class InventoryLotSerializer(serializers.ModelSerializer):
    item_name=serializers.CharField(source='item.name',read_only=True)
    days_to_expiry=serializers.SerializerMethodField()
    def get_days_to_expiry(self,obj):
        if not obj.expires_at:return None
        from django.utils import timezone
        return (obj.expires_at.date()-timezone.localdate()).days
    class Meta:model=InventoryLot;fields='__all__'

class ReservationSerializer(serializers.ModelSerializer):
    table_number=serializers.CharField(source='table.number',read_only=True,allow_null=True)
    branch_name=serializers.CharField(source='branch.name',read_only=True)
    class Meta:model=Reservation;fields='__all__';read_only_fields=['status','created_by','seated_session']

class LoyaltyProgramSerializer(serializers.ModelSerializer):
    class Meta:model=LoyaltyProgram;fields='__all__'
class CustomerLoyaltyAccountSerializer(serializers.ModelSerializer):
    customer_name=serializers.CharField(source='customer.name',read_only=True)
    class Meta:model=CustomerLoyaltyAccount;fields='__all__';read_only_fields=['points_balance','lifetime_points']
class LoyaltyLedgerSerializer(serializers.ModelSerializer):
    class Meta:model=LoyaltyLedger;fields='__all__'
class WalletAccountSerializer(serializers.ModelSerializer):
    customer_name=serializers.CharField(source='customer.name',read_only=True)
    class Meta:model=WalletAccount;fields='__all__';read_only_fields=['balance']
class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:model=WalletTransaction;fields='__all__'

class NotificationSerializer(serializers.ModelSerializer):
    branch_name=serializers.CharField(source='branch.name',read_only=True)
    order_number=serializers.IntegerField(source='order.order_number',read_only=True,allow_null=True)
    class Meta:model=Notification;fields='__all__'
class SmsProviderConfigSerializer(serializers.ModelSerializer):
    api_key=serializers.CharField(write_only=True,required=False,allow_blank=True)
    api_key_configured=serializers.SerializerMethodField()
    def get_api_key_configured(self,obj):return bool(obj.api_key_encrypted)
    def create(self,validated_data):
        secret=validated_data.pop('api_key','');obj=super().create(validated_data)
        if secret:obj.set_api_key(secret);obj.save(update_fields=['api_key_encrypted','updated_at'])
        return obj
    def update(self,instance,validated_data):
        secret=validated_data.pop('api_key',None);obj=super().update(instance,validated_data)
        if secret is not None and secret!='':obj.set_api_key(secret);obj.save(update_fields=['api_key_encrypted','updated_at'])
        return obj
    class Meta:
        model=SmsProviderConfig;fields='__all__';extra_kwargs={'api_key_encrypted':{'write_only':True}}
class PagerProviderConfigSerializer(serializers.ModelSerializer):
    api_key=serializers.CharField(write_only=True,required=False,allow_blank=True)
    api_key_configured=serializers.SerializerMethodField()
    def get_api_key_configured(self,obj):return bool(obj.api_key_encrypted)
    def create(self,validated_data):
        secret=validated_data.pop('api_key','');obj=super().create(validated_data)
        if secret:obj.set_api_key(secret);obj.save(update_fields=['api_key_encrypted','updated_at'])
        return obj
    def update(self,instance,validated_data):
        secret=validated_data.pop('api_key',None);obj=super().update(instance,validated_data)
        if secret:obj.set_api_key(secret);obj.save(update_fields=['api_key_encrypted','updated_at'])
        return obj
    class Meta:
        model=PagerProviderConfig;fields='__all__';extra_kwargs={'api_key_encrypted':{'write_only':True}}

class OnlineMenuSettingsSerializer(serializers.ModelSerializer):
    branch_name=serializers.CharField(source='branch.name',read_only=True)
    class Meta:model=OnlineMenuSettings;fields='__all__'
class TableQrTokenSerializer(serializers.ModelSerializer):
    table_number=serializers.CharField(source='table.number',read_only=True)
    branch_name=serializers.CharField(source='table.hall.branch.name',read_only=True)
    class Meta:model=TableQrToken;fields='__all__';read_only_fields=['token']
class OnlineOrderSerializer(serializers.ModelSerializer):
    order_number=serializers.IntegerField(source='order.order_number',read_only=True)
    grand_total=serializers.DecimalField(source='order.grand_total',max_digits=14,decimal_places=0,read_only=True)
    order_status=serializers.CharField(source='order.status',read_only=True)
    payment_status=serializers.CharField(source='order.payment_status',read_only=True)
    class Meta:model=OnlineOrder;fields='__all__';read_only_fields=['access_token','status']

class BillSplitLineSerializer(serializers.ModelSerializer):
    item_name=serializers.CharField(source='order_item.product_name',read_only=True)
    class Meta:model=BillSplitLine;fields='__all__'
class BillSplitSerializer(serializers.ModelSerializer):
    lines=BillSplitLineSerializer(many=True,read_only=True)
    payments=PaymentSerializer(many=True,read_only=True)
    paid_amount=serializers.SerializerMethodField()
    def get_paid_amount(self,obj):return sum((p.amount for p in obj.payments.all()),0)
    class Meta:model=BillSplit;fields='__all__'


# === FINAL RELEASE serializers ===
from apps.delivery.models import DeliveryZone,DeliveryAddress,CourierProfile,DeliveryAssignment
from apps.giftcards.models import GiftCard,GiftCardTransaction
from apps.payment_gateway.models import PaymentGatewayConfig,GatewayIntent
from apps.loyalty.models import LoyaltyTier,LoyaltyCampaign
from apps.inventory.models import LotInventoryCount,LotInventoryCountLine
from apps.notifications.models import PushProviderConfig,PushSubscription
from apps.dining.models import TableTransferLog

class DeliveryZoneSerializer(serializers.ModelSerializer):
    branch_name=serializers.CharField(source='branch.name',read_only=True)
    class Meta:model=DeliveryZone;fields='__all__'
class DeliveryAddressSerializer(serializers.ModelSerializer):
    zone_name=serializers.CharField(source='zone.name',read_only=True,allow_null=True)
    class Meta:model=DeliveryAddress;fields='__all__'
class CourierProfileSerializer(serializers.ModelSerializer):
    user_name=serializers.CharField(source='user.username',read_only=True,allow_null=True)
    class Meta:model=CourierProfile;fields='__all__'
class DeliveryAssignmentSerializer(serializers.ModelSerializer):
    order_number=serializers.IntegerField(source='order.order_number',read_only=True)
    courier_name=serializers.CharField(source='courier.name',read_only=True,allow_null=True)
    address_text=serializers.CharField(source='address.address',read_only=True)
    zone_name=serializers.CharField(source='zone.name',read_only=True,allow_null=True)
    class Meta:model=DeliveryAssignment;fields='__all__';read_only_fields=['order','address','zone','delivery_fee','assigned_at','picked_up_at','delivered_at']

class GiftCardTransactionSerializer(serializers.ModelSerializer):
    class Meta:model=GiftCardTransaction;fields='__all__'
class GiftCardSerializer(serializers.ModelSerializer):
    transactions=GiftCardTransactionSerializer(many=True,read_only=True)
    masked_code=serializers.SerializerMethodField()
    def get_masked_code(self,obj):return f'****-{obj.code_last4}'
    class Meta:
        model=GiftCard
        fields=['id','uuid','branch','masked_code','initial_balance','balance','expires_at','is_active','purchaser_name','recipient_name','note','created_at','updated_at','transactions']

class PaymentGatewayConfigSerializer(serializers.ModelSerializer):
    merchant_id=serializers.CharField(write_only=True,required=False,allow_blank=True)
    api_key=serializers.CharField(write_only=True,required=False,allow_blank=True)
    merchant_configured=serializers.SerializerMethodField()
    api_key_configured=serializers.SerializerMethodField()
    def get_merchant_configured(self,obj):return bool(obj.merchant_id_encrypted)
    def get_api_key_configured(self,obj):return bool(obj.api_key_encrypted)
    def _secrets(self,obj,data):
        merchant=data.pop('merchant_id',None);api=data.pop('api_key',None)
        if merchant:obj.set_merchant_id(merchant)
        if api:obj.set_api_key(api)
        if merchant or api:obj.save(update_fields=['merchant_id_encrypted','api_key_encrypted','updated_at'])
        return obj
    def create(self,validated_data):
        merchant=validated_data.pop('merchant_id','');api=validated_data.pop('api_key','')
        obj=super().create(validated_data)
        if merchant:obj.set_merchant_id(merchant)
        if api:obj.set_api_key(api)
        if merchant or api:obj.save(update_fields=['merchant_id_encrypted','api_key_encrypted','updated_at'])
        return obj
    def update(self,instance,validated_data):
        merchant=validated_data.pop('merchant_id',None);api=validated_data.pop('api_key',None)
        obj=super().update(instance,validated_data)
        if merchant:obj.set_merchant_id(merchant)
        if api:obj.set_api_key(api)
        if merchant or api:obj.save(update_fields=['merchant_id_encrypted','api_key_encrypted','updated_at'])
        return obj
    class Meta:
        model=PaymentGatewayConfig;fields='__all__'
        extra_kwargs={'merchant_id_encrypted':{'write_only':True},'api_key_encrypted':{'write_only':True}}
class GatewayIntentSerializer(serializers.ModelSerializer):
    order_number=serializers.IntegerField(source='payment.order.order_number',read_only=True)
    amount=serializers.DecimalField(source='payment.amount',max_digits=14,decimal_places=0,read_only=True)
    class Meta:model=GatewayIntent;fields='__all__'

class LoyaltyTierSerializer(serializers.ModelSerializer):
    class Meta:model=LoyaltyTier;fields='__all__'
class LoyaltyCampaignSerializer(serializers.ModelSerializer):
    class Meta:model=LoyaltyCampaign;fields='__all__'

class LotInventoryCountLineSerializer(serializers.ModelSerializer):
    lot_number=serializers.CharField(source='lot.lot_number',read_only=True)
    item_name=serializers.CharField(source='lot.item.name',read_only=True)
    class Meta:model=LotInventoryCountLine;fields='__all__'
class LotInventoryCountSerializer(serializers.ModelSerializer):
    lines=LotInventoryCountLineSerializer(many=True,read_only=True)
    class Meta:model=LotInventoryCount;fields='__all__'

class PushProviderConfigSerializer(serializers.ModelSerializer):
    private_key=serializers.CharField(write_only=True,required=False,allow_blank=True)
    private_key_configured=serializers.SerializerMethodField()
    def get_private_key_configured(self,obj):return bool(obj.vapid_private_key_encrypted)
    def create(self,validated_data):
        secret=validated_data.pop('private_key','');obj=super().create(validated_data)
        if secret:obj.set_private_key(secret);obj.save(update_fields=['vapid_private_key_encrypted','updated_at'])
        return obj
    def update(self,instance,validated_data):
        secret=validated_data.pop('private_key',None);obj=super().update(instance,validated_data)
        if secret:obj.set_private_key(secret);obj.save(update_fields=['vapid_private_key_encrypted','updated_at'])
        return obj
    class Meta:
        model=PushProviderConfig;fields='__all__';extra_kwargs={'vapid_private_key_encrypted':{'write_only':True}}
class PushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:model=PushSubscription;fields='__all__';read_only_fields=['branch','customer','order']

class TableTransferLogSerializer(serializers.ModelSerializer):
    from_number=serializers.CharField(source='from_table.number',read_only=True)
    to_number=serializers.CharField(source='to_table.number',read_only=True)
    class Meta:model=TableTransferLog;fields='__all__'
