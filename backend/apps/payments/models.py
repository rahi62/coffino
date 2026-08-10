from django.db import models
from apps.core.models import TimeStampedModel

class Payment(TimeStampedModel):
    class Method(models.TextChoices):
        CASH='CASH','نقدی'
        POS='POS','کارتخوان'
        ONLINE='ONLINE','آنلاین'
        CREDIT='CREDIT','اعتباری'
        WALLET='WALLET','کیف پول'
        GIFT_CARD='GIFT_CARD','کارت هدیه'
    class Status(models.TextChoices):
        PENDING="PENDING","در انتظار"
        SUCCEEDED="SUCCEEDED","موفق"
        FAILED="FAILED","ناموفق"
        PARTIALLY_REFUNDED="PARTIALLY_REFUNDED","بخشی برگشت"
        REFUNDED="REFUNDED","برگشت کامل"
    order=models.ForeignKey('orders.Order',on_delete=models.CASCADE,related_name='payments')
    amount=models.DecimalField(max_digits=14,decimal_places=0)
    method=models.CharField(max_length=16,choices=Method.choices)
    status=models.CharField(max_length=24,choices=Status.choices,default=Status.SUCCEEDED)
    reference_number=models.CharField(max_length=120,blank=True)
    payer_label=models.CharField(max_length=80,blank=True)
    tendered_amount=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    change_amount=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    bill_split=models.ForeignKey('BillSplit',null=True,blank=True,on_delete=models.SET_NULL,related_name='payments')
    gift_card=models.ForeignKey('giftcards.GiftCard',null=True,blank=True,on_delete=models.SET_NULL,related_name='payments')
    bank_account=models.ForeignKey('accounting.BankAccount',null=True,blank=True,on_delete=models.SET_NULL,related_name='payments')
    received_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL)

class Refund(TimeStampedModel):
    payment=models.ForeignKey(Payment,on_delete=models.PROTECT,related_name='refunds')
    amount=models.DecimalField(max_digits=14,decimal_places=0)
    reason=models.CharField(max_length=250)
    method=models.CharField(max_length=16,choices=Payment.Method.choices)
    reference_number=models.CharField(max_length=120,blank=True)
    created_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL)

class BillSplit(TimeStampedModel):
    class Status(models.TextChoices):OPEN='OPEN','باز';PARTIAL='PARTIAL','بخشی';PAID='PAID','پرداخت';CANCELLED='CANCELLED','لغو'
    order=models.ForeignKey('orders.Order',on_delete=models.CASCADE,related_name='bill_splits')
    label=models.CharField(max_length=80)
    items_subtotal=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    discount_share=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    service_charge_share=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    tax_share=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    total=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.OPEN)
class BillSplitLine(TimeStampedModel):
    split=models.ForeignKey(BillSplit,on_delete=models.CASCADE,related_name='lines')
    order_item=models.ForeignKey('orders.OrderItem',on_delete=models.PROTECT,related_name='split_lines')
    quantity=models.DecimalField(max_digits=10,decimal_places=3)
    subtotal_share=models.DecimalField(max_digits=14,decimal_places=0)
