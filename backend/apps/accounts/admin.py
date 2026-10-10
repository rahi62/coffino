from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ManagerOverrideCredential, OtpChallenge, User


@admin.register(User)
class CafinoUserAdmin(UserAdmin):
    list_display=('username','mobile','business','branch','role','is_staff','is_active')
    list_filter=('mobile_verified_at','business','branch','role','is_staff','is_active')
    fieldsets=UserAdmin.fieldsets+(
        ('هویت و محدوده کافینو',{'fields':('mobile','mobile_verified_at','tokens_invalid_before','business','branch','role','permission_overrides')}),
    )
    add_fieldsets=UserAdmin.add_fieldsets+(
        ('هویت و محدوده کافینو',{'fields':('mobile','business','branch','role')}),
    )


@admin.register(OtpChallenge)
class OtpChallengeAdmin(admin.ModelAdmin):
    list_display=('uuid','purpose','masked_mobile','delivery_status','failed_attempts','expires_at','consumed_at')
    list_filter=('purpose','delivery_status','consumed_at')
    search_fields=('uuid','correlation_id')
    readonly_fields=[field.name for field in OtpChallenge._meta.fields]

    @admin.display(description='شماره همراه')
    def masked_mobile(self,obj):
        from .phone import mask_mobile
        return mask_mobile(obj.mobile)

    def has_add_permission(self,request):
        return False

    def has_change_permission(self,request,obj=None):
        return False


@admin.register(ManagerOverrideCredential)
class ManagerOverrideCredentialAdmin(admin.ModelAdmin):
    list_display=('user','is_active','updated_at')
    readonly_fields=('pin_hash','updated_at')
