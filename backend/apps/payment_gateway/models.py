from django.db import models
from apps.core.models import TimeStampedModel

class PaymentGatewayConfig(TimeStampedModel):
    class Provider(models.TextChoices):
        MOCK='MOCK','Mock/Development'
        ZARINPAL='ZARINPAL','ZarinPal'
        GENERIC='GENERIC','Generic HTTP'
    branch=models.OneToOneField('businesses.Branch',on_delete=models.CASCADE,related_name='payment_gateway')
    provider=models.CharField(max_length=20,choices=Provider.choices,default=Provider.MOCK)
    is_active=models.BooleanField(default=False)
    merchant_id_encrypted=models.TextField(blank=True)
    api_key_encrypted=models.TextField(blank=True)
    request_url=models.URLField(blank=True)
    verify_url=models.URLField(blank=True)
    refund_url=models.URLField(blank=True)
    gateway_url=models.URLField(blank=True)
    callback_base_url=models.URLField(blank=True)
    sandbox=models.BooleanField(default=False)
    timeout_seconds=models.PositiveIntegerField(default=15)
    extra=models.JSONField(default=dict,blank=True)
    def set_merchant_id(self,value):
        from apps.notifications.crypto import encrypt_secret
        self.merchant_id_encrypted=encrypt_secret(value)
    def get_merchant_id(self):
        from apps.notifications.crypto import decrypt_secret
        return decrypt_secret(self.merchant_id_encrypted)
    def set_api_key(self,value):
        from apps.notifications.crypto import encrypt_secret
        self.api_key_encrypted=encrypt_secret(value)
    def get_api_key(self):
        from apps.notifications.crypto import decrypt_secret
        return decrypt_secret(self.api_key_encrypted)

class GatewayIntent(TimeStampedModel):
    class Status(models.TextChoices):
        CREATED='CREATED','ایجاد'
        REDIRECTED='REDIRECTED','هدایت'
        VERIFIED='VERIFIED','تأیید'
        FAILED='FAILED','ناموفق'
        CANCELLED='CANCELLED','لغو'
    payment=models.OneToOneField('payments.Payment',on_delete=models.CASCADE,related_name='gateway_intent')
    provider=models.CharField(max_length=20)
    authority=models.CharField(max_length=160,blank=True,db_index=True)
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.CREATED)
    payment_url=models.URLField(blank=True)
    callback_url=models.URLField(blank=True)
    request_payload=models.JSONField(default=dict,blank=True)
    verify_payload=models.JSONField(default=dict,blank=True)
    reference_id=models.CharField(max_length=120,blank=True)
    verified_at=models.DateTimeField(null=True,blank=True)
