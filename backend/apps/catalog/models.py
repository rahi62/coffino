from django.db import models
from apps.core.models import TimeStampedModel

class Category(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='categories')
    name=models.CharField(max_length=120)
    sort_order=models.PositiveIntegerField(default=0)
    is_active=models.BooleanField(default=True)
    def __str__(self): return self.name

class Product(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='products')
    category=models.ForeignKey(Category,null=True,blank=True,on_delete=models.SET_NULL,related_name='products')
    name=models.CharField(max_length=160)
    product_type=models.CharField(max_length=24,default='PREPARED_ITEM')
    sku=models.CharField(max_length=80,blank=True)
    price=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    is_available=models.BooleanField(default=True)
    preparation_station=models.ForeignKey('kitchen.PreparationStation',null=True,blank=True,on_delete=models.SET_NULL,related_name='products')
    stock_item=models.ForeignKey('inventory.InventoryItem',null=True,blank=True,on_delete=models.SET_NULL,related_name='sale_products')
    def __str__(self): return self.name
