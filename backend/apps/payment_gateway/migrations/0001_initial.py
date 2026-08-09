from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='PaymentGatewayConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('provider', models.CharField(max_length=20, choices=[('MOCK', 'Mock/Development'), ('ZARINPAL', 'ZarinPal'), ('GENERIC', 'Generic HTTP')], default='MOCK')),
                ('is_active', models.BooleanField(default=False)),
                ('merchant_id_encrypted', models.TextField(blank=True)),
                ('api_key_encrypted', models.TextField(blank=True)),
                ('request_url', models.URLField(blank=True)),
                ('verify_url', models.URLField(blank=True)),
                ('refund_url', models.URLField(blank=True)),
                ('gateway_url', models.URLField(blank=True)),
                ('callback_base_url', models.URLField(blank=True)),
                ('sandbox', models.BooleanField(default=False)),
                ('timeout_seconds', models.PositiveIntegerField(default=15)),
                ('extra', models.JSONField(default=dict, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='GatewayIntent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('provider', models.CharField(max_length=20)),
                ('authority', models.CharField(max_length=160, blank=True, db_index=True)),
                ('status', models.CharField(max_length=20, choices=[('CREATED', 'ایجاد'), ('REDIRECTED', 'هدایت'), ('VERIFIED', 'تأیید'), ('FAILED', 'ناموفق'), ('CANCELLED', 'لغو')], default='CREATED')),
                ('payment_url', models.URLField(blank=True)),
                ('callback_url', models.URLField(blank=True)),
                ('request_payload', models.JSONField(default=dict, blank=True)),
                ('verify_payload', models.JSONField(default=dict, blank=True)),
                ('reference_id', models.CharField(max_length=120, blank=True)),
                ('verified_at', models.DateTimeField(null=True, blank=True)),
            ]
        ),
    ]
