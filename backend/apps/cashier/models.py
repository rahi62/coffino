from django.db import models
from apps.core.models import TimeStampedModel

class CashRegister(TimeStampedModel):
    branch=models.ForeignKey("businesses.Branch",on_delete=models.CASCADE,related_name="cash_registers")
    name=models.CharField(max_length=120)
    is_active=models.BooleanField(default=True)
    def __str__(self): return self.name

class CashShift(TimeStampedModel):
    register=models.ForeignKey(CashRegister,on_delete=models.CASCADE,related_name="shifts")
    cashier=models.ForeignKey("accounts.User",null=True,blank=True,on_delete=models.SET_NULL)
    opening_balance=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    expected_cash=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    closing_balance=models.DecimalField(max_digits=14,decimal_places=0,null=True,blank=True)
    difference=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    is_open=models.BooleanField(default=True)
    opened_at=models.DateTimeField(auto_now_add=True)
    closed_at=models.DateTimeField(null=True,blank=True)

class CashMovement(TimeStampedModel):
    class Type(models.TextChoices):
        SALE="SALE","فروش نقدی"
        REFUND="REFUND","برگشت وجه نقدی"
        CASH_IN="CASH_IN","ورود نقد"
        CASH_OUT="CASH_OUT","خروج نقد"
        EXPENSE="EXPENSE","هزینه نقدی"
        SUPPLIER_PAYMENT="SUPPLIER_PAYMENT","پرداخت نقدی تامین‌کننده"
        ADJUSTMENT="ADJUSTMENT","اصلاح"
    shift=models.ForeignKey(CashShift,on_delete=models.CASCADE,related_name="movements")
    movement_type=models.CharField(max_length=24,choices=Type.choices)
    amount=models.DecimalField(max_digits=14,decimal_places=0)
    note=models.CharField(max_length=250,blank=True)
    payment=models.ForeignKey("payments.Payment",null=True,blank=True,on_delete=models.SET_NULL)
    reference_type=models.CharField(max_length=40,blank=True)
    reference_id=models.CharField(max_length=64,blank=True)
    created_by=models.ForeignKey("accounts.User",null=True,blank=True,on_delete=models.SET_NULL)

class DailyClosing(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='daily_closings')
    business_date=models.DateField()
    gross_sales=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    refunds=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    net_sales=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    cash_sales=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    pos_sales=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    expenses=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    expected_cash=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    counted_cash=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    cash_difference=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    closed_by=models.ForeignKey('accounts.User',null=True,on_delete=models.SET_NULL)
    closed_at=models.DateTimeField(auto_now_add=True)
    snapshot=models.JSONField(default=dict,blank=True)
    class Meta:
        unique_together=('branch','business_date')
        ordering=['-business_date']
