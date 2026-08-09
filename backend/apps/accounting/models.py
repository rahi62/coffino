from django.db import models
from apps.core.models import TimeStampedModel
class ExpenseCategory(TimeStampedModel):
    branch=models.ForeignKey("businesses.Branch",on_delete=models.CASCADE,related_name="expense_categories")
    name=models.CharField(max_length=120)
    def __str__(self): return self.name

class Expense(TimeStampedModel):
    branch=models.ForeignKey("businesses.Branch",on_delete=models.CASCADE,related_name="expenses")
    category=models.ForeignKey(ExpenseCategory,null=True,blank=True,on_delete=models.SET_NULL,related_name="expenses")
    title=models.CharField(max_length=160)
    amount=models.DecimalField(max_digits=14,decimal_places=0)
    payment_method=models.CharField(max_length=24,default="CASH")
    occurred_at=models.DateTimeField()
    notes=models.TextField(blank=True)
    created_by=models.ForeignKey("accounts.User",null=True,blank=True,on_delete=models.SET_NULL)

class FixedOverhead(TimeStampedModel):
    class Frequency(models.TextChoices):
        DAILY="DAILY","روزانه"; MONTHLY="MONTHLY","ماهانه"; YEARLY="YEARLY","سالانه"
    branch=models.ForeignKey("businesses.Branch",on_delete=models.CASCADE,related_name="fixed_overheads")
    title=models.CharField(max_length=160)
    amount=models.DecimalField(max_digits=14,decimal_places=0)
    frequency=models.CharField(max_length=16,choices=Frequency.choices,default=Frequency.MONTHLY)
    is_active=models.BooleanField(default=True)

class FiscalSettings(TimeStampedModel):
    branch=models.OneToOneField('businesses.Branch',on_delete=models.CASCADE,related_name='fiscal_settings')
    tax_rate=models.DecimalField(max_digits=6,decimal_places=3,default=0)
    service_charge_rate=models.DecimalField(max_digits=6,decimal_places=3,default=0)
    prices_include_tax=models.BooleanField(default=False)
    service_charge_order_types=models.JSONField(default=list,blank=True)
    tax_enabled=models.BooleanField(default=False)
    service_charge_enabled=models.BooleanField(default=False)
    service_charge_is_revenue=models.BooleanField(default=True)
    delivery_fee_taxable=models.BooleanField(default=False)
    receipt_tax_label=models.CharField(max_length=80,default='مالیات')
    receipt_service_label=models.CharField(max_length=80,default='حق سرویس')
