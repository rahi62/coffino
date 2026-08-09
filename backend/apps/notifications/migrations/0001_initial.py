from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='SmsProviderConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('provider_name', models.CharField(max_length=80, default='GENERIC_HTTP')),
                ('endpoint_url', models.URLField(blank=True)),
                ('api_key_encrypted', models.TextField(blank=True)),
                ('headers', models.JSONField(default=dict, blank=True)),
                ('sender', models.CharField(max_length=80, blank=True)),
                ('phone_field', models.CharField(max_length=40, default='to')),
                ('message_field', models.CharField(max_length=40, default='message')),
                ('sender_field', models.CharField(max_length=40, default='sender')),
                ('is_active', models.BooleanField(default=False)),
                ('timeout_seconds', models.PositiveIntegerField(default=10)),
            ]
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('channel', models.CharField(max_length=16, choices=[('IN_APP', 'داخل برنامه'), ('SMS', 'پیامک'), ('PUSH', 'Push')])),
                ('event', models.CharField(max_length=60)),
                ('recipient', models.CharField(max_length=160, blank=True)),
                ('title', models.CharField(max_length=160, blank=True)),
                ('body', models.TextField()),
                ('status', models.CharField(max_length=16, choices=[('PENDING', 'در انتظار'), ('PROCESSING', 'در حال ارسال'), ('SENT', 'ارسال شده'), ('FAILED', 'خطا'), ('CANCELLED', 'لغو')], default='PENDING')),
                ('attempts', models.PositiveIntegerField(default=0)),
                ('next_attempt_at', models.DateTimeField(null=True, blank=True)),
                ('last_error', models.TextField(blank=True)),
                ('sent_at', models.DateTimeField(null=True, blank=True)),
                ('dedupe_key', models.CharField(max_length=160, blank=True)),
            ],
            options={'ordering': ['-created_at']}
        ),
        migrations.CreateModel(
            name='PushProviderConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('vapid_public_key', models.TextField(blank=True)),
                ('vapid_private_key_encrypted', models.TextField(blank=True)),
                ('subject', models.CharField(max_length=160, default='mailto:admin@cafino.local')),
                ('is_active', models.BooleanField(default=False)),
            ]
        ),
        migrations.CreateModel(
            name='PushSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('endpoint', models.TextField()),
                ('p256dh', models.TextField()),
                ('auth', models.TextField()),
                ('user_agent', models.CharField(max_length=250, blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ]
        ),
    ]
