import secrets
from uuid import uuid4

from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .models import ManagerOverrideCredential, OtpChallenge, PlatformOtpProviderConfig, User
from .otp_providers import OtpDeliveryError, sender_from_platform_config
from .phone import normalize_iran_mobile


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


class PlatformOtpProviderConfigForm(forms.ModelForm):
    test_mobile = forms.CharField(
        label="شماره همراه آزمایشی",
        required=False,
        max_length=32,
        help_text="نمونه: 09123456789",
    )
    api_key = forms.CharField(
        label="API Key",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="برای حفظ مقدار فعلی خالی بگذارید.",
    )
    signature = forms.CharField(
        label="Signature",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="برای حفظ مقدار فعلی خالی بگذارید.",
    )

    class Meta:
        model = PlatformOtpProviderConfig
        fields = (
            "provider",
            "enabled",
            "api_base_url",
            "api_key",
            "signature",
            "add_name",
            "timeout_seconds",
            "test_mobile",
        )

    def clean_test_mobile(self):
        value = self.cleaned_data.get("test_mobile", "")
        return normalize_iran_mobile(value) if value else ""

    def save(self, commit=True):
        obj = super().save(commit=False)
        api_key = self.cleaned_data.get("api_key")
        signature = self.cleaned_data.get("signature")
        if api_key:
            obj.set_api_key(api_key)
        if signature:
            obj.set_signature(signature)
        if commit:
            obj.save()
        return obj


@admin.register(PlatformOtpProviderConfig)
class PlatformOtpProviderConfigAdmin(admin.ModelAdmin):
    form = PlatformOtpProviderConfigForm
    list_display = ("provider", "enabled", "credentials_state", "test_mobile", "updated_at")
    list_filter = ("provider", "enabled")
    readonly_fields = ("credentials_state", "uuid", "created_at", "updated_at")
    actions = ("send_test_otp",)

    fieldsets = (
        ("Provider سراسری OTP", {
            "fields": ("provider", "enabled", "api_base_url", "add_name", "timeout_seconds"),
            "description": "این تنظیمات Global است و به هیچ شعبه‌ای تعلق ندارد. با ایجاد این رکورد، تنظیمات DB بر env اولویت دارد.",
        }),
        ("Credentials", {
            "fields": ("api_key", "credentials_state"),
            "description": "برای OTP پارس‌گرین فقط API Key لازم است. مقدار ذخیره‌شده نمایش داده نمی‌شود؛ خالی بگذارید تا حفظ شود.",
        }),
        ("ارسال آزمایشی", {"fields": ("test_mobile",)}),
        ("Audit", {"fields": ("uuid", "created_at", "updated_at")}),
    )

    @admin.display(description="وضعیت Credential", boolean=True)
    def credentials_state(self, obj):
        return bool(obj and obj.credentials_configured)

    def get_queryset(self, request):
        return super().get_queryset(request)

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        # Keep permission checks DB-free because Admin localization contracts
        # exercise the registry from SimpleTestCase. The unique provider field
        # and ModelForm validation prevent duplicate global rows.
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    @admin.action(description="ارسال OTP آزمایشی به شماره تست")
    def send_test_otp(self, request, queryset):
        for config in queryset:
            if not config.test_mobile:
                self.message_user(
                    request,
                    "شماره تست تنظیم نشده است.",
                    level=messages.WARNING,
                )
                continue
            try:
                sender_from_platform_config(config).send(
                    mobile=config.test_mobile,
                    code=f"{secrets.randbelow(1_000_000):06d}",
                    correlation_id=str(uuid4()),
                )
            except OtpDeliveryError:
                self.message_user(
                    request,
                    "ارسال آزمایشی ناموفق بود. فعال بودن Provider و Credentialها را بررسی کنید.",
                    level=messages.ERROR,
                )
                continue
            self.message_user(
                request,
                f"OTP آزمایشی به {config.test_mobile} ارسال شد.",
                level=messages.SUCCESS,
            )


@admin.register(ManagerOverrideCredential)
class ManagerOverrideCredentialAdmin(admin.ModelAdmin):
    list_display=('user','is_active','updated_at')
    readonly_fields=('pin_hash','updated_at')
