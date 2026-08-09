from django.db import models
from apps.core.models import TimeStampedModel

class GiftCard(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='gift_cards')
    code_hash=models.CharField(max_length=64,db_index=True)
    code_last4=models.CharField(max_length=4)
    initial_balance=models.DecimalField(max_digits=14,decimal_places=0)
    balance=models.DecimalField(max_digits=14,decimal_places=0)
    expires_at=models.DateTimeField(null=True,blank=True)
    is_active=models.BooleanField(default=True)
    purchaser_name=models.CharField(max_length=140,blank=True)
    recipient_name=models.CharField(max_length=140,blank=True)
    note=models.CharField(max_length=250,blank=True)

class GiftCardTransaction(TimeStampedModel):
    class Type(models.TextChoices):
        ISSUE='ISSUE','صدور'
        DEBIT='DEBIT','مصرف'
        REFUND='REFUND','برگشت'
        ADJUST='ADJUST','اصلاح'
    card=models.ForeignKey(GiftCard,on_delete=models.PROTECT,related_name='transactions')
    order=models.ForeignKey('orders.Order',null=True,blank=True,on_delete=models.SET_NULL,related_name='gift_card_transactions')
    transaction_type=models.CharField(max_length=16,choices=Type.choices)
    amount=models.DecimalField(max_digits=14,decimal_places=0)
    balance_after=models.DecimalField(max_digits=14,decimal_places=0)
    reference=models.CharField(max_length=100,blank=True)
