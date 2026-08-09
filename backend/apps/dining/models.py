from django.db import models
from apps.core.models import TimeStampedModel
class Hall(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='halls')
    name=models.CharField(max_length=120)
class Table(TimeStampedModel):
    class Status(models.TextChoices):
        FREE="FREE","آزاد"
        OCCUPIED="OCCUPIED","مشغول"
        RESERVED="RESERVED","رزرو"
    hall=models.ForeignKey(Hall,on_delete=models.CASCADE,related_name='tables')
    number=models.CharField(max_length=24)
    capacity=models.PositiveIntegerField(default=2)
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.FREE)
class TableSession(TimeStampedModel):
    table=models.ForeignKey(Table,on_delete=models.CASCADE,related_name='sessions')
    customer_count=models.PositiveIntegerField(default=1)
    opened_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL)
    opened_at=models.DateTimeField(auto_now_add=True)
    closed_at=models.DateTimeField(null=True,blank=True)
    is_open=models.BooleanField(default=True)

class TableTransferLog(TimeStampedModel):
    session=models.ForeignKey(TableSession,on_delete=models.PROTECT,related_name='transfer_logs')
    from_table=models.ForeignKey(Table,on_delete=models.PROTECT,related_name='transfers_out')
    to_table=models.ForeignKey(Table,on_delete=models.PROTECT,related_name='transfers_in')
    transferred_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL)
