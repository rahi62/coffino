from django.db import models
from apps.core.models import TimeStampedModel
class AuditLog(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',null=True,blank=True,on_delete=models.SET_NULL,related_name='audit_logs')
    actor=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL,related_name='audit_logs')
    action=models.CharField(max_length=80)
    entity_type=models.CharField(max_length=80)
    entity_id=models.CharField(max_length=80,blank=True)
    description=models.CharField(max_length=300,blank=True)
    before=models.JSONField(default=dict,blank=True)
    after=models.JSONField(default=dict,blank=True)
    metadata=models.JSONField(default=dict,blank=True)
    ip_address=models.GenericIPAddressField(null=True,blank=True)
    class Meta: ordering=['-created_at']
