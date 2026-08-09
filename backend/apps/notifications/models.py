from django.db import models
from apps.core.models import TimeStampedModel
class SmsProviderConfig(TimeStampedModel):
    branch=models.OneToOneField('businesses.Branch',on_delete=models.CASCADE,related_name='sms_provider')
    provider_name=models.CharField(max_length=80,default='GENERIC_HTTP')
    endpoint_url=models.URLField(blank=True)
    api_key_encrypted=models.TextField(blank=True)
    headers=models.JSONField(default=dict,blank=True)
    sender=models.CharField(max_length=80,blank=True)
    phone_field=models.CharField(max_length=40,default='to')
    message_field=models.CharField(max_length=40,default='message')
    sender_field=models.CharField(max_length=40,default='sender')
    is_active=models.BooleanField(default=False)
    timeout_seconds=models.PositiveIntegerField(default=10)
    @property
    def api_key(self):
        from .crypto import decrypt_secret
        return decrypt_secret(self.api_key_encrypted)
    def set_api_key(self,value):
        from .crypto import encrypt_secret
        self.api_key_encrypted=encrypt_secret(value)
class Notification(TimeStampedModel):
    class Channel(models.TextChoices):IN_APP='IN_APP','داخل برنامه';SMS='SMS','پیامک';PUSH='PUSH','Push'
    class Status(models.TextChoices):PENDING='PENDING','در انتظار';PROCESSING='PROCESSING','در حال ارسال';SENT='SENT','ارسال شده';FAILED='FAILED','خطا';CANCELLED='CANCELLED','لغو'
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='notifications')
    customer=models.ForeignKey('customers.Customer',null=True,blank=True,on_delete=models.SET_NULL,related_name='notifications')
    order=models.ForeignKey('orders.Order',null=True,blank=True,on_delete=models.SET_NULL,related_name='notifications')
    channel=models.CharField(max_length=16,choices=Channel.choices)
    event=models.CharField(max_length=60)
    recipient=models.CharField(max_length=160,blank=True)
    title=models.CharField(max_length=160,blank=True)
    body=models.TextField()
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.PENDING)
    attempts=models.PositiveIntegerField(default=0)
    next_attempt_at=models.DateTimeField(null=True,blank=True)
    last_error=models.TextField(blank=True)
    sent_at=models.DateTimeField(null=True,blank=True)
    dedupe_key=models.CharField(max_length=160,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['branch','dedupe_key'],condition=~models.Q(dedupe_key=''),name='uniq_notification_dedupe_branch')]
        ordering=['-created_at']

class PushProviderConfig(TimeStampedModel):
    branch=models.OneToOneField('businesses.Branch',on_delete=models.CASCADE,related_name='push_provider')
    vapid_public_key=models.TextField(blank=True)
    vapid_private_key_encrypted=models.TextField(blank=True)
    subject=models.CharField(max_length=160,default='mailto:admin@cafino.local')
    is_active=models.BooleanField(default=False)
    def set_private_key(self,value):
        from .crypto import encrypt_secret
        self.vapid_private_key_encrypted=encrypt_secret(value)
    def get_private_key(self):
        from .crypto import decrypt_secret
        return decrypt_secret(self.vapid_private_key_encrypted)

class PushSubscription(TimeStampedModel):
    branch=models.ForeignKey('businesses.Branch',on_delete=models.CASCADE,related_name='push_subscriptions')
    customer=models.ForeignKey('customers.Customer',null=True,blank=True,on_delete=models.CASCADE,related_name='push_subscriptions')
    order=models.ForeignKey('orders.Order',null=True,blank=True,on_delete=models.CASCADE,related_name='push_subscriptions')
    endpoint=models.TextField()
    p256dh=models.TextField()
    auth=models.TextField()
    user_agent=models.CharField(max_length=250,blank=True)
    is_active=models.BooleanField(default=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['branch','endpoint'],name='uniq_push_endpoint_branch')]
