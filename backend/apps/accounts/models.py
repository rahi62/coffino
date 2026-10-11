import uuid

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import TimeStampedModel

from .phone import normalize_iran_mobile

class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER='OWNER','مالک'
        MANAGER='MANAGER','مدیر'
        CASHIER='CASHIER','صندوق‌دار'
        WAITER='WAITER','گارسون'
        KITCHEN='KITCHEN','آشپزخانه'
        INVENTORY='INVENTORY','انباردار'
        ACCOUNTANT='ACCOUNTANT','حسابدار'

    business=models.ForeignKey(
        'businesses.Business',null=True,blank=True,on_delete=models.PROTECT,related_name='users'
    )
    branch=models.ForeignKey(
        'businesses.Branch',null=True,blank=True,on_delete=models.PROTECT,related_name='users'
    )
    role=models.CharField(max_length=32,choices=Role.choices,default=Role.CASHIER)
    permission_overrides=models.JSONField(default=dict,blank=True)
    mobile=models.CharField(max_length=11,null=True,blank=True,unique=True)
    mobile_verified_at=models.DateTimeField(null=True,blank=True)
    tokens_invalid_before=models.DateTimeField(null=True,blank=True)

    OPERATIONAL_ROLES={Role.CASHIER,Role.WAITER,Role.KITCHEN,Role.INVENTORY,Role.ACCOUNTANT}

    def clean(self):
        super().clean()
        if self.mobile:
            self.mobile=normalize_iran_mobile(self.mobile)
        else:
            self.mobile=None
        # A selected branch is authoritative for its business and can fill it in.
        if self.branch_id:
            branch_business_id=self.branch.business_id
            if not self.business_id:
                self.business_id=branch_business_id
            elif self.business_id!=branch_business_id:
                raise ValidationError({'branch':'شعبه باید متعلق به کسب‌وکار کاربر باشد.'})

        if self.is_superuser:
            return

        if not self.business_id:
            raise ValidationError({'business':'کاربر غیر سراسری باید به یک کسب‌وکار متصل باشد.'})

        if self.role in self.OPERATIONAL_ROLES and not self.branch_id:
            raise ValidationError({'branch':'نقش عملیاتی باید شعبه مشخص داشته باشد.'})

    def save(self,*args,**kwargs):
        self.clean()
        return super().save(*args,**kwargs)

    class Meta:
        constraints=[
            models.CheckConstraint(
                condition=(
                    Q(is_superuser=True) |
                    (
                        Q(business__isnull=False) &
                        (Q(role__in=['OWNER','MANAGER']) | Q(branch__isnull=False))
                    )
                ),
                name='user_tenant_scope_required',
            )
        ]


class OtpChallenge(TimeStampedModel):
    class Purpose(models.TextChoices):
        SAAS_REGISTRATION='SAAS_REGISTRATION','ثبت‌نام کسب‌وکار'
        STAFF_LOGIN='STAFF_LOGIN','ورود کاربر پنل'
        PASSWORD_RECOVERY='PASSWORD_RECOVERY','بازیابی رمز عبور'
        CUSTOMER_VERIFY='CUSTOMER_VERIFY','تأیید شماره مشتری'

    class DeliveryStatus(models.TextChoices):
        PENDING='PENDING','در انتظار ارسال'
        SENT='SENT','ارسال شده'
        FAILED='FAILED','ناموفق'

    mobile=models.CharField(max_length=11,db_index=True)
    purpose=models.CharField(max_length=32,choices=Purpose.choices,db_index=True)
    code_hash=models.CharField(max_length=256)
    expires_at=models.DateTimeField(db_index=True)
    next_send_at=models.DateTimeField()
    failed_attempts=models.PositiveSmallIntegerField(default=0)
    max_attempts=models.PositiveSmallIntegerField(default=5)
    verified_at=models.DateTimeField(null=True,blank=True)
    consumed_at=models.DateTimeField(null=True,blank=True)
    user=models.ForeignKey(
        User,null=True,blank=True,on_delete=models.SET_NULL,related_name='otp_challenges'
    )
    business=models.ForeignKey(
        'businesses.Business',null=True,blank=True,on_delete=models.SET_NULL,related_name='otp_challenges'
    )
    delivery_status=models.CharField(
        max_length=16,choices=DeliveryStatus.choices,default=DeliveryStatus.PENDING
    )
    provider_code=models.CharField(max_length=64,blank=True)
    correlation_id=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    request_fingerprint=models.CharField(max_length=64,blank=True,db_index=True)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_consumed(self):
        return self.consumed_at is not None

    @property
    def is_locked(self):
        return self.failed_attempts >= self.max_attempts

    class Meta:
        ordering=['-created_at']

class ManagerOverrideCredential(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='manager_override')
    pin_hash=models.CharField(max_length=200)
    is_active=models.BooleanField(default=True)
    updated_at=models.DateTimeField(auto_now=True)



class PlatformOtpProviderConfig(TimeStampedModel):
    class Provider(models.TextChoices):
        PARSGREEN = "PARSGREEN", "ParsGreen"

    provider = models.CharField(
        max_length=32,
        choices=Provider.choices,
        default=Provider.PARSGREEN,
        unique=True,
    )
    enabled = models.BooleanField(default=False)
    api_base_url = models.URLField(default="https://sms.parsgreen.ir")
    api_key_encrypted = models.TextField(blank=True)
    signature_encrypted = models.TextField(blank=True)
    add_name = models.BooleanField(default=True)
    timeout_seconds = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
    )
    test_mobile = models.CharField(max_length=11, blank=True)

    def clean(self):
        super().clean()
        if self.api_base_url and not self.api_base_url.lower().startswith("https://"):
            raise ValidationError({"api_base_url": "آدرس Provider باید با HTTPS باشد."})
        if self.test_mobile:
            self.test_mobile = normalize_iran_mobile(self.test_mobile)

    def set_api_key(self, value):
        from apps.notifications.crypto import encrypt_secret
        self.api_key_encrypted = encrypt_secret(value)

    def get_api_key(self):
        from apps.notifications.crypto import decrypt_secret
        return decrypt_secret(self.api_key_encrypted)

    def set_signature(self, value):
        from apps.notifications.crypto import encrypt_secret
        self.signature_encrypted = encrypt_secret(value)

    def get_signature(self):
        from apps.notifications.crypto import decrypt_secret
        return decrypt_secret(self.signature_encrypted)

    @property
    def credentials_configured(self):
        return bool(self.get_api_key() and self.get_signature())

    def __str__(self):
        return f"OTP Provider — {self.get_provider_display()}"
