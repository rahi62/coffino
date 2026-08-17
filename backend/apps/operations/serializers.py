from rest_framework import serializers

from .models import DeviceInstallation, DiagnosticRequest, ReleasePolicy


class DeviceSerializer(serializers.ModelSerializer):
    business_name=serializers.CharField(source='business.name',read_only=True,allow_null=True)
    branch_name=serializers.CharField(source='branch.name',read_only=True,allow_null=True)
    online=serializers.SerializerMethodField()

    class Meta:
        model=DeviceInstallation
        fields=[
            'id','installation_id','business','business_name','branch','branch_name',
            'license_id','customer_label','machine_hash','current_version','release_channel',
            'platform','arch','app_health','telemetry_enabled','last_seen_at','last_backup_at',
            'last_backup_ok','last_update_status','last_crash_at','is_active','online','created_at','updated_at',
        ]
        read_only_fields=fields

    def get_online(self,obj):
        from django.utils import timezone
        return bool(obj.last_seen_at and (timezone.now()-obj.last_seen_at).total_seconds()<=15*60)


class ReleasePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model=ReleasePolicy
        fields=[
            'id','channel','target_version','minimum_version','rollback_version','rollout_percent',
            'paused','blocked_versions','advisory_message','required_after','updated_at',
        ]
        read_only_fields=['id','updated_at']

    def validate_rollout_percent(self,value):
        if value<0 or value>100:
            raise serializers.ValidationError('Rollout percent must be between 0 and 100.')
        return value

    def validate_blocked_versions(self,value):
        if not isinstance(value,list) or len(value)>100:
            raise serializers.ValidationError('blocked_versions must be a list with at most 100 entries.')
        clean=[]
        for item in value:
            text=str(item).strip()
            if not text or len(text)>40:
                raise serializers.ValidationError('Invalid blocked version.')
            clean.append(text)
        return clean


class DiagnosticRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model=DiagnosticRequest
        fields=['request_id','status','requested_by_label','expires_at','completed_at','snapshot','created_at']
        read_only_fields=fields
