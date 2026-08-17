from django.contrib import admin

from .models import DeviceEvent, DeviceInstallation, DiagnosticRequest, ReleasePolicy


@admin.register(DeviceInstallation)
class DeviceInstallationAdmin(admin.ModelAdmin):
    list_display=('license_id','current_version','release_channel','app_health','business','branch','last_seen_at','is_active')
    list_filter=('release_channel','app_health','telemetry_enabled','is_active')
    search_fields=('license_id','customer_label','machine_hash','installation_id')
    readonly_fields=('token_hash','machine_hash','installation_id','last_seen_at','last_crash_at','created_at','updated_at')


@admin.register(ReleasePolicy)
class ReleasePolicyAdmin(admin.ModelAdmin):
    list_display=('channel','target_version','rollout_percent','paused','minimum_version','rollback_version')


@admin.register(DeviceEvent)
class DeviceEventAdmin(admin.ModelAdmin):
    list_display=('event_type','severity','app_version','component','installation','occurred_at')
    readonly_fields=('installation','event_type','severity','app_version','component','code','fingerprint','occurred_at','created_at','updated_at')


@admin.register(DiagnosticRequest)
class DiagnosticRequestAdmin(admin.ModelAdmin):
    list_display=('request_id','installation','status','requested_by_label','created_at','completed_at')
    readonly_fields=('request_id','installation','status','requested_by_label','expires_at','completed_at','snapshot','created_at','updated_at')
