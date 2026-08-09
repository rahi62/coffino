from django.db import models
from apps.core.models import TimeStampedModel

class DeliveryZone(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='delivery_zones')
    name=models.CharField(max_length=140)
    code=models.CharField(max_length=60)
    delivery_fee=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    min_order_amount=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    free_delivery_above=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    estimated_minutes=models.PositiveIntegerField(default=35)
    is_active=models.BooleanField(default=True)
    class Meta:unique_together=('branch','code')
    def __str__(self):return self.name

class DeliveryAddress(TimeStampedModel):
    customer=models.ForeignKey('customers.Customer',null=True,blank=True,on_delete=models.CASCADE,related_name='delivery_addresses')
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='delivery_addresses')
    zone=models.ForeignKey(DeliveryZone,null=True,blank=True,on_delete=models.SET_NULL,related_name='addresses')
    title=models.CharField(max_length=80,blank=True)
    recipient_name=models.CharField(max_length=140)
    phone=models.CharField(max_length=24)
    address=models.TextField()
    postal_code=models.CharField(max_length=20,blank=True)
    latitude=models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)
    longitude=models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)
    notes=models.CharField(max_length=250,blank=True)

class CourierProfile(TimeStampedModel):
    class Status(models.TextChoices):
        AVAILABLE='AVAILABLE','آماده'
        BUSY='BUSY','مشغول'
        OFFLINE='OFFLINE','آفلاین'
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='couriers')
    user=models.OneToOneField('accounts.User',null=True,blank=True,on_delete=models.SET_NULL,related_name='courier_profile')
    name=models.CharField(max_length=140)
    phone=models.CharField(max_length=24,blank=True)
    vehicle=models.CharField(max_length=80,blank=True)
    plate=models.CharField(max_length=40,blank=True)
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.AVAILABLE)
    is_active=models.BooleanField(default=True)

class DeliveryAssignment(TimeStampedModel):
    class Status(models.TextChoices):
        WAITING='WAITING','در انتظار پیک'
        ASSIGNED='ASSIGNED','اختصاص داده شد'
        PICKED_UP='PICKED_UP','تحویل از مجموعه'
        DELIVERED='DELIVERED','تحویل مشتری'
        FAILED='FAILED','ناموفق'
        CANCELLED='CANCELLED','لغو'
    order=models.OneToOneField('orders.Order',on_delete=models.CASCADE,related_name='delivery_assignment')
    address=models.ForeignKey(DeliveryAddress,on_delete=models.PROTECT,related_name='assignments')
    courier=models.ForeignKey(CourierProfile,null=True,blank=True,on_delete=models.SET_NULL,related_name='assignments')
    zone=models.ForeignKey(DeliveryZone,null=True,blank=True,on_delete=models.SET_NULL)
    delivery_fee=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.WAITING)
    assigned_at=models.DateTimeField(null=True,blank=True)
    picked_up_at=models.DateTimeField(null=True,blank=True)
    delivered_at=models.DateTimeField(null=True,blank=True)
    proof_note=models.CharField(max_length=250,blank=True)
