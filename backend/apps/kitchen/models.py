from django.db import models
from apps.core.models import TimeStampedModel
class PreparationStation(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='stations')
    name=models.CharField(max_length=120)
    code=models.CharField(max_length=40)
    is_active=models.BooleanField(default=True)
    def __str__(self): return self.name
class KitchenTicket(TimeStampedModel):
    class Status(models.TextChoices):
        NEW="NEW","جدید"
        PREPARING="PREPARING","در حال آماده‌سازی"
        READY="READY","آماده"
        DONE="DONE","تحویل/بسته"
    order=models.ForeignKey('orders.Order',on_delete=models.CASCADE,related_name='kitchen_tickets')
    station=models.ForeignKey(PreparationStation,on_delete=models.CASCADE,related_name='tickets')
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.NEW)
