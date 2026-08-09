from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

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

    OPERATIONAL_ROLES={Role.CASHIER,Role.WAITER,Role.KITCHEN,Role.INVENTORY,Role.ACCOUNTANT}

    def clean(self):
        super().clean()
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

class ManagerOverrideCredential(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='manager_override')
    pin_hash=models.CharField(max_length=200)
    is_active=models.BooleanField(default=True)
    updated_at=models.DateTimeField(auto_now=True)
