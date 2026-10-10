from django.db import models
from apps.core.models import TimeStampedModel
class Customer(TimeStampedModel):
 branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='customers'); name=models.CharField(max_length=160,default='مشتری گذری'); phone=models.CharField(max_length=20,blank=True); phone_normalized=models.CharField(max_length=11,null=True,blank=True,db_index=True); phone_verified_at=models.DateTimeField(null=True,blank=True); notes=models.TextField(blank=True); is_walk_in=models.BooleanField(default=False)
