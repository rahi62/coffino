from django.db import models
from apps.core.models import TimeStampedModel
class DiscountRule(TimeStampedModel):
    class Trigger(models.TextChoices):
        AUTO='AUTO','خودکار'; CODE='CODE','کد تخفیف'
    class Scope(models.TextChoices):
        ORDER='ORDER','کل سفارش'; CATEGORY='CATEGORY','دسته'; PRODUCT='PRODUCT','محصول'
    class Kind(models.TextChoices):
        PERCENT='PERCENT','درصدی'; FIXED='FIXED','مبلغ ثابت'
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='discount_rules')
    name=models.CharField(max_length=140)
    code=models.CharField(max_length=40,blank=True)
    trigger=models.CharField(max_length=12,choices=Trigger.choices,default=Trigger.AUTO)
    scope=models.CharField(max_length=16,choices=Scope.choices,default=Scope.ORDER)
    category=models.ForeignKey('catalog.Category',null=True,blank=True,on_delete=models.CASCADE)
    product=models.ForeignKey('catalog.Product',null=True,blank=True,on_delete=models.CASCADE)
    kind=models.CharField(max_length=12,choices=Kind.choices,default=Kind.PERCENT)
    value=models.DecimalField(max_digits=14,decimal_places=2)
    min_order_amount=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    max_discount=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    starts_at=models.DateTimeField(null=True,blank=True)
    ends_at=models.DateTimeField(null=True,blank=True)
    weekdays=models.JSONField(default=list,blank=True,help_text='0=Monday ... 6=Sunday; empty means all')
    priority=models.IntegerField(default=100)
    is_active=models.BooleanField(default=True)
    requires_manager=models.BooleanField(default=False)
    def __str__(self): return self.name
