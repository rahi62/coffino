import uuid

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
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
