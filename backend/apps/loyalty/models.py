from django.db import models
from apps.core.models import TimeStampedModel
class LoyaltyProgram(TimeStampedModel):
    branch=models.OneToOneField('businesses.Branch',on_delete=models.CASCADE,related_name='loyalty_program')
    is_active=models.BooleanField(default=True)
    amount_per_point=models.DecimalField(max_digits=14,decimal_places=0,default=100000)
    point_wallet_value=models.DecimalField(max_digits=14,decimal_places=0,default=10000)
    min_redeem_points=models.PositiveIntegerField(default=10)
    welcome_points=models.PositiveIntegerField(default=0)
class CustomerLoyaltyAccount(TimeStampedModel):
    customer=models.OneToOneField('customers.Customer',on_delete=models.CASCADE,related_name='loyalty_account')
    points_balance=models.IntegerField(default=0)
    lifetime_points=models.PositiveIntegerField(default=0)
    tier=models.CharField(max_length=40,default='STANDARD')
class LoyaltyLedger(TimeStampedModel):
    class Type(models.TextChoices):EARN='EARN','کسب';REDEEM='REDEEM','مصرف';ADJUST='ADJUST','اصلاح';EXPIRE='EXPIRE','انقضا'
    account=models.ForeignKey(CustomerLoyaltyAccount,on_delete=models.CASCADE,related_name='ledger')
    order=models.ForeignKey('orders.Order',null=True,blank=True,on_delete=models.SET_NULL,related_name='loyalty_entries')
    entry_type=models.CharField(max_length=16,choices=Type.choices)
    points=models.IntegerField()
    balance_after=models.IntegerField()
    note=models.CharField(max_length=250,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['account','order','entry_type'],condition=models.Q(order__isnull=False),name='uniq_loyalty_order_type')]
class WalletAccount(TimeStampedModel):
    customer=models.OneToOneField('customers.Customer',on_delete=models.CASCADE,related_name='wallet')
    balance=models.DecimalField(max_digits=14,decimal_places=0,default=0)
class WalletTransaction(TimeStampedModel):
    class Type(models.TextChoices):CREDIT='CREDIT','واریز';DEBIT='DEBIT','برداشت';REFUND='REFUND','برگشت';ADJUST='ADJUST','اصلاح';LOYALTY='LOYALTY','تبدیل امتیاز'
    wallet=models.ForeignKey(WalletAccount,on_delete=models.CASCADE,related_name='transactions')
    order=models.ForeignKey('orders.Order',null=True,blank=True,on_delete=models.SET_NULL,related_name='wallet_transactions')
    transaction_type=models.CharField(max_length=16,choices=Type.choices)
    amount=models.DecimalField(max_digits=14,decimal_places=0)
    balance_after=models.DecimalField(max_digits=14,decimal_places=0)
    reference=models.CharField(max_length=100,blank=True)
    note=models.CharField(max_length=250,blank=True)

class LoyaltyTier(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='loyalty_tiers')
    name=models.CharField(max_length=80)
    code=models.CharField(max_length=40)
    min_lifetime_points=models.PositiveIntegerField(default=0)
    points_multiplier=models.DecimalField(max_digits=6,decimal_places=2,default=1)
    priority=models.PositiveIntegerField(default=100)
    is_active=models.BooleanField(default=True)
    class Meta:
        unique_together=('branch','code')
        ordering=['min_lifetime_points','priority']

class LoyaltyCampaign(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='loyalty_campaigns')
    name=models.CharField(max_length=120)
    points_multiplier=models.DecimalField(max_digits=6,decimal_places=2,default=1)
    bonus_points=models.PositiveIntegerField(default=0)
    starts_at=models.DateTimeField()
    ends_at=models.DateTimeField()
    order_types=models.JSONField(default=list,blank=True)
    is_active=models.BooleanField(default=True)
