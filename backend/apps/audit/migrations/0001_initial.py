from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('action', models.CharField(max_length=80)),
                ('entity_type', models.CharField(max_length=80)),
                ('entity_id', models.CharField(max_length=80, blank=True)),
                ('description', models.CharField(max_length=300, blank=True)),
                ('before', models.JSONField(default=dict, blank=True)),
                ('after', models.JSONField(default=dict, blank=True)),
                ('metadata', models.JSONField(default=dict, blank=True)),
                ('ip_address', models.GenericIPAddressField(null=True, blank=True)),
            ],
            options={'ordering': ['-created_at']}
        ),
    ]
