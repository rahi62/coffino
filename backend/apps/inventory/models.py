from django.db import models
from apps.core.models import TimeStampedModel

class IngredientCategory(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='ingredient_categories')
    name=models.CharField(max_length=80)
    sort_order=models.PositiveIntegerField(default=0)
    is_active=models.BooleanField(default=True)
    class Meta:
        unique_together=('branch','name')
        ordering=['sort_order','name','id']
    def __str__(self):return self.name

class InventoryItem(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='inventory_items')
    name=models.CharField(max_length=160)
    category=models.CharField(max_length=80,blank=True,default='')
    material_category=models.ForeignKey(IngredientCategory,null=True,blank=True,on_delete=models.SET_NULL,related_name='materials')
    unit=models.CharField(max_length=24,default='gram')
    current_stock=models.DecimalField(max_digits=14,decimal_places=3,default=0)
    minimum_stock=models.DecimalField(max_digits=14,decimal_places=3,default=0)
    average_cost=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    last_purchase_cost=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    item_code=models.CharField(max_length=80,blank=True)
    lot_tracked=models.BooleanField(default=False)
    shelf_life_days=models.PositiveIntegerField(default=0)
    is_active=models.BooleanField(default=True)

class StockMovement(TimeStampedModel):
    class Type(models.TextChoices):
        PURCHASE='PURCHASE','خرید'
        SALE='SALE_CONSUMPTION','مصرف فروش'
        WASTE='WASTE','ضایعات'
        ADJUSTMENT='ADJUSTMENT','اصلاح'
        RETURN='RETURN','برگشت'
        PRODUCTION='PRODUCTION','تولید'
        TRANSFER_IN='TRANSFER_IN','انتقال ورودی'
        TRANSFER_OUT='TRANSFER_OUT','انتقال خروجی'
    item=models.ForeignKey(InventoryItem,on_delete=models.PROTECT,related_name='movements')
    movement_type=models.CharField(max_length=24,choices=Type.choices)
    quantity=models.DecimalField(max_digits=14,decimal_places=3)
    reason=models.CharField(max_length=250,blank=True)
    unit_cost=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    reference_type=models.CharField(max_length=40,blank=True)
    reference_id=models.CharField(max_length=64,blank=True)
    lot=models.ForeignKey('InventoryLot',null=True,blank=True,on_delete=models.SET_NULL,related_name='movements')

class RecipeItem(TimeStampedModel):
    product=models.ForeignKey('catalog.Product',on_delete=models.CASCADE,related_name='recipe_items')
    inventory_item=models.ForeignKey(InventoryItem,on_delete=models.PROTECT,related_name='recipe_usages')
    quantity=models.DecimalField(max_digits=14,decimal_places=3)

class WasteRecord(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='waste_records')
    item=models.ForeignKey(InventoryItem,on_delete=models.PROTECT,related_name='waste_records')
    quantity=models.DecimalField(max_digits=14,decimal_places=3)
    unit_cost=models.DecimalField(max_digits=14,decimal_places=2)
    total_cost=models.DecimalField(max_digits=14,decimal_places=2)
    reason=models.CharField(max_length=160)
    note=models.CharField(max_length=250,blank=True)
    created_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL)

class InventoryCount(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT='DRAFT','پیش‌نویس'
        POSTED='POSTED','ثبت نهایی'
        CANCELLED='CANCELLED','لغو'
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='inventory_counts')
    title=models.CharField(max_length=160)
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.DRAFT)
    counted_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL,related_name='inventory_counts')
    posted_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL,related_name='posted_inventory_counts')
    posted_at=models.DateTimeField(null=True,blank=True)
    notes=models.TextField(blank=True)

class InventoryCountLine(TimeStampedModel):
    count=models.ForeignKey(InventoryCount,on_delete=models.CASCADE,related_name='lines')
    item=models.ForeignKey(InventoryItem,on_delete=models.PROTECT,related_name='count_lines')
    system_quantity=models.DecimalField(max_digits=14,decimal_places=3)
    counted_quantity=models.DecimalField(max_digits=14,decimal_places=3)
    variance=models.DecimalField(max_digits=14,decimal_places=3,default=0)
    unit_cost_snapshot=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    variance_value=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    class Meta:
        unique_together=('count','item')

class StockTransfer(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT='DRAFT','پیش‌نویس'
        POSTED='POSTED','ثبت نهایی'
        CANCELLED='CANCELLED','لغو'
    source_branch=models.ForeignKey('businesses.Branch',on_delete=models.PROTECT,related_name='outgoing_stock_transfers')
    destination_branch=models.ForeignKey('businesses.Branch',on_delete=models.PROTECT,related_name='incoming_stock_transfers')
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.DRAFT)
    requested_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL,related_name='requested_stock_transfers')
    posted_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL,related_name='posted_stock_transfers')
    posted_at=models.DateTimeField(null=True,blank=True)
    reference=models.CharField(max_length=80,blank=True)
    notes=models.TextField(blank=True)

class StockTransferLine(TimeStampedModel):
    transfer=models.ForeignKey(StockTransfer,on_delete=models.CASCADE,related_name='lines')
    source_item=models.ForeignKey(InventoryItem,on_delete=models.PROTECT,related_name='transfer_out_lines')
    destination_item=models.ForeignKey(InventoryItem,on_delete=models.PROTECT,related_name='transfer_in_lines')
    quantity=models.DecimalField(max_digits=14,decimal_places=3)
    unit_cost_snapshot=models.DecimalField(max_digits=14,decimal_places=2,default=0)

class InventoryLot(TimeStampedModel):
    item=models.ForeignKey(InventoryItem,on_delete=models.PROTECT,related_name='lots')
    lot_number=models.CharField(max_length=100)
    received_at=models.DateTimeField(auto_now_add=True)
    expires_at=models.DateTimeField(null=True,blank=True)
    quantity_received=models.DecimalField(max_digits=14,decimal_places=3)
    quantity_remaining=models.DecimalField(max_digits=14,decimal_places=3)
    unit_cost=models.DecimalField(max_digits=14,decimal_places=2)
    source_type=models.CharField(max_length=40,blank=True)
    source_id=models.CharField(max_length=64,blank=True)
    is_blocked=models.BooleanField(default=False)
    notes=models.CharField(max_length=250,blank=True)
    class Meta:
        unique_together=('item','lot_number')
        ordering=['expires_at','received_at','id']

class LotInventoryCount(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT='DRAFT','پیش‌نویس'
        POSTED='POSTED','ثبت نهایی'
        CANCELLED='CANCELLED','لغو'
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='lot_inventory_counts')
    title=models.CharField(max_length=160)
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.DRAFT)
    counted_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL,related_name='lot_counts')
    posted_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL,related_name='posted_lot_counts')
    posted_at=models.DateTimeField(null=True,blank=True)
    notes=models.TextField(blank=True)

class LotInventoryCountLine(TimeStampedModel):
    count=models.ForeignKey(LotInventoryCount,on_delete=models.CASCADE,related_name='lines')
    lot=models.ForeignKey(InventoryLot,on_delete=models.PROTECT,related_name='count_lines')
    system_quantity=models.DecimalField(max_digits=14,decimal_places=3)
    counted_quantity=models.DecimalField(max_digits=14,decimal_places=3)
    variance=models.DecimalField(max_digits=14,decimal_places=3,default=0)
    variance_value=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    class Meta:unique_together=('count','lot')
