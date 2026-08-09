from django.db import models
from apps.core.models import TimeStampedModel
class Supplier(TimeStampedModel):
    branch=models.ForeignKey("businesses.Branch",on_delete=models.CASCADE,related_name="suppliers")
    name=models.CharField(max_length=160)
    phone=models.CharField(max_length=32,blank=True)
    address=models.TextField(blank=True)
    opening_balance=models.DecimalField(max_digits=14,decimal_places=0,default=0)
    is_active=models.BooleanField(default=True)
    def __str__(self): return self.name
