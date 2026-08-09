from django.contrib import admin
from .models import AuditLog
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display=('created_at','actor','action','entity_type','entity_id','branch')
    list_filter=('action','entity_type','branch')
    search_fields=('description','entity_id','actor__username')
