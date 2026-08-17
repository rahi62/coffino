import uuid

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class DeviceInstallation(TimeStampedModel):
    class Channel(models.TextChoices):
        STABLE='stable','Stable'
        BETA='beta','Beta'

    class Health(models.TextChoices):
        UNKNOWN='unknown','Unknown'
        HEALTHY='healthy','Healthy'
        DEGRADED='degraded','Degraded'

    installation_id=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    token_hash=models.CharField(max_length=64,unique=True)
    business=models.ForeignKey('businesses.Business',null=True,blank=True,on_delete=models.SET_NULL,related_name='device_installations')
    branch=models.ForeignKey('businesses.Branch',null=True,blank=True,on_delete=models.SET_NULL,related_name='device_installations')
    license_id=models.CharField(max_length=120,db_index=True)
    customer_label=models.CharField(max_length=160,blank=True)
    machine_hash=models.CharField(max_length=64,db_index=True)
    current_version=models.CharField(max_length=40,blank=True)
    release_channel=models.CharField(max_length=12,choices=Channel.choices,default=Channel.STABLE)
    platform=models.CharField(max_length=32,blank=True)
    arch=models.CharField(max_length=32,blank=True)
    app_health=models.CharField(max_length=16,choices=Health.choices,default=Health.UNKNOWN)
    telemetry_enabled=models.BooleanField(default=False)
    last_seen_at=models.DateTimeField(null=True,blank=True)
    last_backup_at=models.DateTimeField(null=True,blank=True)
    last_backup_ok=models.BooleanField(null=True,blank=True)
    last_update_status=models.CharField(max_length=32,blank=True)
    last_crash_at=models.DateTimeField(null=True,blank=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        ordering=['-last_seen_at','-updated_at']
        constraints=[
            models.UniqueConstraint(fields=['license_id','machine_hash'],name='ops_device_license_machine_unique'),
        ]

    def __str__(self):
        return f'{self.license_id} · {self.installation_id}'


class ReleasePolicy(TimeStampedModel):
    channel=models.CharField(max_length=12,choices=DeviceInstallation.Channel.choices,unique=True)
    target_version=models.CharField(max_length=40,blank=True)
    minimum_version=models.CharField(max_length=40,blank=True)
    rollback_version=models.CharField(max_length=40,blank=True)
    rollout_percent=models.PositiveSmallIntegerField(default=100)
    paused=models.BooleanField(default=False)
    blocked_versions=models.JSONField(default=list,blank=True)
    advisory_message=models.TextField(blank=True)
    required_after=models.DateTimeField(null=True,blank=True)

    class Meta:
        ordering=['channel']
        constraints=[
            models.CheckConstraint(
                condition=models.Q(rollout_percent__gte=0,rollout_percent__lte=100),
                name='ops_release_rollout_percent_range',
            ),
        ]

    def __str__(self):
        return f'{self.channel}: {self.target_version or "no target"}'


class DeviceEvent(TimeStampedModel):
    class Type(models.TextChoices):
        STARTUP_HEALTHY='startup_healthy','Startup healthy'
        UPDATE_SUCCESS='update_success','Update success'
        UPDATE_FAILED='update_failed','Update failed'
        BACKUP_FAILED='backup_failed','Backup failed'
        CRASH='crash','Crash'
        RECOVERY_REQUIRED='recovery_required','Recovery required'
        LICENSE_INVALID='license_invalid','License invalid'

    class Severity(models.TextChoices):
        INFO='info','Info'
        WARNING='warning','Warning'
        ERROR='error','Error'
        CRITICAL='critical','Critical'

    installation=models.ForeignKey(DeviceInstallation,on_delete=models.CASCADE,related_name='events')
    event_type=models.CharField(max_length=32,choices=Type.choices)
    severity=models.CharField(max_length=12,choices=Severity.choices,default=Severity.INFO)
    app_version=models.CharField(max_length=40,blank=True)
    component=models.CharField(max_length=48,blank=True)
    code=models.CharField(max_length=80,blank=True)
    fingerprint=models.CharField(max_length=64,blank=True,db_index=True)
    occurred_at=models.DateTimeField(default=timezone.now,db_index=True)

    class Meta:
        ordering=['-occurred_at']
        indexes=[
            models.Index(fields=['event_type','occurred_at'],name='ops_event_type_time_idx'),
            models.Index(fields=['app_version','occurred_at'],name='ops_event_version_time_idx'),
        ]


class DiagnosticRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING='pending','Pending'
        COMPLETED='completed','Completed'
        EXPIRED='expired','Expired'
        CANCELLED='cancelled','Cancelled'

    request_id=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    installation=models.ForeignKey(DeviceInstallation,on_delete=models.CASCADE,related_name='diagnostic_requests')
    status=models.CharField(max_length=16,choices=Status.choices,default=Status.PENDING)
    requested_by_label=models.CharField(max_length=160,blank=True)
    expires_at=models.DateTimeField(null=True,blank=True)
    completed_at=models.DateTimeField(null=True,blank=True)
    snapshot=models.JSONField(default=dict,blank=True)

    class Meta:
        ordering=['-created_at']

    def is_expired(self):
        return bool(self.expires_at and self.expires_at<=timezone.now())
