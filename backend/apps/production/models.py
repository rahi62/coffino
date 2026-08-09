from django.db import models
from apps.core.models import TimeStampedModel

class ProductionFormula(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='production_formulas')
    name=models.CharField(max_length=160)
    output_item=models.ForeignKey('inventory.InventoryItem',on_delete=models.PROTECT,related_name='production_formulas')
    output_quantity=models.DecimalField(max_digits=14,decimal_places=3,default=1)
    is_active=models.BooleanField(default=True)
    notes=models.TextField(blank=True)
    def __str__(self): return self.name

class ProductionFormulaItem(TimeStampedModel):
    formula=models.ForeignKey(ProductionFormula,on_delete=models.CASCADE,related_name='ingredients')
    inventory_item=models.ForeignKey('inventory.InventoryItem',on_delete=models.PROTECT,related_name='production_formula_usages')
    quantity=models.DecimalField(max_digits=14,decimal_places=3)

class ProductionBatch(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT='DRAFT','پیش‌نویس'
        POSTED='POSTED','تولید شده'
        CANCELLED='CANCELLED','لغو'
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='production_batches')
    formula=models.ForeignKey(ProductionFormula,on_delete=models.PROTECT,related_name='batches')
    batch_number=models.CharField(max_length=80,blank=True)
    multiplier=models.DecimalField(max_digits=14,decimal_places=3,default=1)
    produced_quantity=models.DecimalField(max_digits=14,decimal_places=3,default=0)
    total_cost=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    unit_cost=models.DecimalField(max_digits=14,decimal_places=2,default=0)
    expires_at=models.DateTimeField(null=True,blank=True)
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.DRAFT)
    created_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL,related_name='created_production_batches')
    posted_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL,related_name='posted_production_batches')
    posted_at=models.DateTimeField(null=True,blank=True)
    notes=models.TextField(blank=True)

class ProductionBatchIngredient(TimeStampedModel):
    batch=models.ForeignKey(ProductionBatch,on_delete=models.CASCADE,related_name='ingredient_snapshots')
    inventory_item=models.ForeignKey('inventory.InventoryItem',on_delete=models.PROTECT)
    quantity=models.DecimalField(max_digits=14,decimal_places=3)
    unit_cost=models.DecimalField(max_digits=14,decimal_places=2)
    total_cost=models.DecimalField(max_digits=14,decimal_places=2)
