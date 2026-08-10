from django.db import models
from apps.core.models import TimeStampedModel
class PagerDevice(TimeStampedModel):
    class Status(models.TextChoices):
        AVAILABLE="AVAILABLE","آزاد"
        ASSIGNED="ASSIGNED","اختصاص یافته"
        DISABLED="DISABLED","غیرفعال"
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='pagers')
    number=models.CharField(max_length=32)
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.AVAILABLE)
class TakeawayProfile(TimeStampedModel):
    class ReadyNotificationMethod(models.TextChoices):
        SMS="SMS","پیامک"
        PAGER="PAGER","پیجر"
        NONE="NONE","بدون اعلان"
    order=models.OneToOneField('orders.Order',on_delete=models.CASCADE,related_name='takeaway_profile')
    pickup_number=models.CharField(max_length=32)
    customer_name=models.CharField(max_length=120,blank=True)
    customer_phone=models.CharField(max_length=20,blank=True)
    pager=models.ForeignKey(PagerDevice,null=True,blank=True,on_delete=models.SET_NULL,related_name='assignments')
    ready_notification_method=models.CharField(max_length=12,choices=ReadyNotificationMethod.choices,default=ReadyNotificationMethod.SMS)
    notified_at=models.DateTimeField(null=True,blank=True)
