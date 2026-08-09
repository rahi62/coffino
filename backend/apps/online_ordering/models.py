import uuid
from django.db import models
from apps.core.models import TimeStampedModel
class OnlineMenuSettings(TimeStampedModel):
    class PaymentMode(models.TextChoices):PAY_AT_COUNTER='PAY_AT_COUNTER','پرداخت صندوق';ONLINE='ONLINE','آنلاین'
    branch=models.OneToOneField('businesses.Branch',on_delete=models.CASCADE,related_name='online_menu_settings')
    public_slug=models.SlugField(max_length=100,unique=True)
    is_enabled=models.BooleanField(default=False)
    accepting_orders=models.BooleanField(default=False)
    payment_mode=models.CharField(max_length=24,choices=PaymentMode.choices,default=PaymentMode.PAY_AT_COUNTER)
    allow_takeaway=models.BooleanField(default=True)
    allow_pickup=models.BooleanField(default=True)
    allow_dine_in_qr=models.BooleanField(default=True)
    allow_delivery=models.BooleanField(default=False)
    public_base_url=models.URLField(default='http://127.0.0.1:3000')
    estimated_minutes=models.PositiveIntegerField(default=20)
    min_order_amount=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    welcome_text=models.CharField(max_length=250,blank=True)
class TableQrToken(TimeStampedModel):
    table=models.OneToOneField('dining.Table',on_delete=models.CASCADE,related_name='qr_token')
    token=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    is_active=models.BooleanField(default=True)
class OnlineOrder(TimeStampedModel):
    class Status(models.TextChoices):PAYMENT_PENDING='PAYMENT_PENDING','در انتظار پرداخت';RECEIVED='RECEIVED','دریافت';ACCEPTED='ACCEPTED','پذیرفته';REJECTED='REJECTED','رد';READY='READY','آماده';COMPLETED='COMPLETED','تکمیل'
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='online_orders')
    order=models.OneToOneField('orders.Order',on_delete=models.CASCADE,related_name='online_order')
    access_token=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    table_token=models.ForeignKey(TableQrToken,null=True,blank=True,on_delete=models.SET_NULL)
    source=models.CharField(max_length=20,default='WEB')
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.RECEIVED)
    customer_name=models.CharField(max_length=160,blank=True)
    customer_phone=models.CharField(max_length=24,blank=True)
    payment_mode=models.CharField(max_length=24)
    estimated_minutes=models.PositiveIntegerField(default=20)
    delivery_address=models.ForeignKey('delivery.DeliveryAddress',null=True,blank=True,on_delete=models.SET_NULL,related_name='online_orders')
