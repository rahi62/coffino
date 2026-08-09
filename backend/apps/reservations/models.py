from django.db import models
from apps.core.models import TimeStampedModel
class Reservation(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING='PENDING','در انتظار';CONFIRMED='CONFIRMED','تأیید';SEATED='SEATED','مستقر';COMPLETED='COMPLETED','تکمیل';CANCELLED='CANCELLED','لغو';NO_SHOW='NO_SHOW','عدم مراجعه'
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='reservations')
    table=models.ForeignKey('dining.Table',null=True,blank=True,on_delete=models.SET_NULL,related_name='reservations')
    customer=models.ForeignKey('customers.Customer',null=True,blank=True,on_delete=models.SET_NULL,related_name='reservations')
    customer_name=models.CharField(max_length=160)
    phone=models.CharField(max_length=24,blank=True)
    party_size=models.PositiveIntegerField(default=2)
    reserved_for=models.DateTimeField()
    duration_minutes=models.PositiveIntegerField(default=90)
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.PENDING)
    source=models.CharField(max_length=24,default='STAFF')
    notes=models.TextField(blank=True)
    created_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL)
    seated_session=models.OneToOneField('dining.TableSession',null=True,blank=True,on_delete=models.SET_NULL,related_name='reservation')
    class Meta:ordering=['reserved_for']
