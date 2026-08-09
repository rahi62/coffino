from django.db import models
from apps.core.models import TimeStampedModel
class Business(TimeStampedModel):
 name=models.CharField(max_length=160); business_type=models.CharField(max_length=32,default='CAFE'); deployment_type=models.CharField(max_length=16,default='LOCAL'); is_active=models.BooleanField(default=True)
 def __str__(self): return self.name
class Branch(TimeStampedModel):
 business=models.ForeignKey(Business,on_delete=models.CASCADE,related_name='branches'); name=models.CharField(max_length=160); address=models.TextField(blank=True); phone=models.CharField(max_length=32,blank=True); is_active=models.BooleanField(default=True)
 def __str__(self): return f'{self.business} - {self.name}'
class BusinessModule(TimeStampedModel):
 business=models.ForeignKey(Business,on_delete=models.CASCADE,related_name='modules'); key=models.CharField(max_length=64); enabled=models.BooleanField(default=True); config=models.JSONField(default=dict,blank=True)
 class Meta: unique_together=('business','key')
