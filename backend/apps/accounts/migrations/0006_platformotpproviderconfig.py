# Generated for Cafino SaaS Identity Foundation

import uuid

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_otpchallenge_verified_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlatformOtpProviderConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("provider", models.CharField(choices=[("PARSGREEN", "ParsGreen")], default="PARSGREEN", max_length=32, unique=True)),
                ("enabled", models.BooleanField(default=False)),
                ("api_base_url", models.URLField(default="https://sms.parsgreen.ir")),
                ("api_key_encrypted", models.TextField(blank=True)),
                ("signature_encrypted", models.TextField(blank=True)),
                ("add_name", models.BooleanField(default=True)),
                ("timeout_seconds", models.PositiveIntegerField(default=10, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(60)])),
                ("test_mobile", models.CharField(blank=True, max_length=11)),
            ],
        ),
    ]
