import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
        ('notifications', '0003_constraints'),
    ]

    operations = [
        migrations.CreateModel(
            name='PagerProviderConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('provider_name', models.CharField(default='GENERIC_HTTP', max_length=80)),
                ('endpoint_url', models.URLField(blank=True)),
                ('api_key_encrypted', models.TextField(blank=True)),
                ('headers', models.JSONField(blank=True, default=dict)),
                ('pager_field', models.CharField(default='pager', max_length=40)),
                ('message_field', models.CharField(default='message', max_length=40)),
                ('is_active', models.BooleanField(default=False)),
                ('timeout_seconds', models.PositiveIntegerField(default=10)),
                ('branch', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='pager_provider', to='businesses.branch')),
            ],
        ),
        migrations.AlterField(
            model_name='notification', name='channel',
            field=models.CharField(choices=[('IN_APP', 'داخل برنامه'), ('SMS', 'پیامک'), ('PAGER', 'پیجر'), ('PUSH', 'اعلان مرورگر')], max_length=16),
        ),
    ]
