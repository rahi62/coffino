import uuid

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial=True
    dependencies=[]
    operations=[
        migrations.CreateModel(
            name='DeviceInstallation',
            fields=[
                ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
                ('uuid',models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),
                ('created_at',models.DateTimeField(auto_now_add=True)),
                ('updated_at',models.DateTimeField(auto_now=True)),
                ('installation_id',models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),
                ('token_hash',models.CharField(max_length=64,unique=True)),
                ('license_id',models.CharField(db_index=True,max_length=120)),
                ('customer_label',models.CharField(blank=True,max_length=160)),
                ('machine_hash',models.CharField(db_index=True,max_length=64)),
                ('current_version',models.CharField(blank=True,max_length=40)),
                ('release_channel',models.CharField(choices=[('stable','Stable'),('beta','Beta')],default='stable',max_length=12)),
                ('platform',models.CharField(blank=True,max_length=32)),
                ('arch',models.CharField(blank=True,max_length=32)),
                ('app_health',models.CharField(choices=[('unknown','Unknown'),('healthy','Healthy'),('degraded','Degraded')],default='unknown',max_length=16)),
                ('telemetry_enabled',models.BooleanField(default=False)),
                ('last_seen_at',models.DateTimeField(blank=True,null=True)),
                ('last_backup_at',models.DateTimeField(blank=True,null=True)),
                ('last_backup_ok',models.BooleanField(blank=True,null=True)),
                ('last_update_status',models.CharField(blank=True,max_length=32)),
                ('last_crash_at',models.DateTimeField(blank=True,null=True)),
                ('is_active',models.BooleanField(default=True)),
            ],
            options={'ordering':['-last_seen_at','-updated_at']},
        ),
        migrations.CreateModel(
            name='ReleasePolicy',
            fields=[
                ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
                ('uuid',models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),
                ('created_at',models.DateTimeField(auto_now_add=True)),
                ('updated_at',models.DateTimeField(auto_now=True)),
                ('channel',models.CharField(choices=[('stable','Stable'),('beta','Beta')],max_length=12,unique=True)),
                ('target_version',models.CharField(blank=True,max_length=40)),
                ('minimum_version',models.CharField(blank=True,max_length=40)),
                ('rollback_version',models.CharField(blank=True,max_length=40)),
                ('rollout_percent',models.PositiveSmallIntegerField(default=100)),
                ('paused',models.BooleanField(default=False)),
                ('blocked_versions',models.JSONField(blank=True,default=list)),
                ('advisory_message',models.TextField(blank=True)),
                ('required_after',models.DateTimeField(blank=True,null=True)),
            ],
            options={'ordering':['channel']},
        ),
        migrations.CreateModel(
            name='DeviceEvent',
            fields=[
                ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
                ('uuid',models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),
                ('created_at',models.DateTimeField(auto_now_add=True)),
                ('updated_at',models.DateTimeField(auto_now=True)),
                ('event_type',models.CharField(choices=[('startup_healthy','Startup healthy'),('update_success','Update success'),('update_failed','Update failed'),('backup_failed','Backup failed'),('crash','Crash'),('recovery_required','Recovery required'),('license_invalid','License invalid')],max_length=32)),
                ('severity',models.CharField(choices=[('info','Info'),('warning','Warning'),('error','Error'),('critical','Critical')],default='info',max_length=12)),
                ('app_version',models.CharField(blank=True,max_length=40)),
                ('component',models.CharField(blank=True,max_length=48)),
                ('code',models.CharField(blank=True,max_length=80)),
                ('fingerprint',models.CharField(blank=True,db_index=True,max_length=64)),
                ('occurred_at',models.DateTimeField(db_index=True,default=django.utils.timezone.now)),
                ('installation',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='events',to='operations.deviceinstallation')),
            ],
            options={
                'ordering':['-occurred_at'],
                'indexes':[models.Index(fields=['event_type','occurred_at'],name='ops_event_type_time_idx'),models.Index(fields=['app_version','occurred_at'],name='ops_event_version_time_idx')],
            },
        ),
        migrations.CreateModel(
            name='DiagnosticRequest',
            fields=[
                ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
                ('uuid',models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),
                ('created_at',models.DateTimeField(auto_now_add=True)),
                ('updated_at',models.DateTimeField(auto_now=True)),
                ('request_id',models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),
                ('status',models.CharField(choices=[('pending','Pending'),('completed','Completed'),('expired','Expired'),('cancelled','Cancelled')],default='pending',max_length=16)),
                ('requested_by_label',models.CharField(blank=True,max_length=160)),
                ('expires_at',models.DateTimeField(blank=True,null=True)),
                ('completed_at',models.DateTimeField(blank=True,null=True)),
                ('snapshot',models.JSONField(blank=True,default=dict)),
                ('installation',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='diagnostic_requests',to='operations.deviceinstallation')),
            ],
            options={'ordering':['-created_at']},
        ),
    ]
