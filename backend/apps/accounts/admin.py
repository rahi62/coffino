from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ManagerOverrideCredential, User


@admin.register(User)
class CafinoUserAdmin(UserAdmin):
    list_display=('username','business','branch','role','is_staff','is_active')
    list_filter=('business','branch','role','is_staff','is_active')
    fieldsets=UserAdmin.fieldsets+(
        ('Cafino tenant',{'fields':('business','branch','role','permission_overrides')}),
    )
    add_fieldsets=UserAdmin.add_fieldsets+(
        ('Cafino tenant',{'fields':('business','branch','role')}),
    )


@admin.register(ManagerOverrideCredential)
class ManagerOverrideCredentialAdmin(admin.ModelAdmin):
    list_display=('user','is_active','updated_at')
    readonly_fields=('pin_hash','updated_at')
