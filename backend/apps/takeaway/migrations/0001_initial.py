from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='PagerDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('number', models.CharField(max_length=32)),
                ('status', models.CharField(max_length=16, choices=[('AVAILABLE', 'آزاد'), ('ASSIGNED', 'اختصاص یافته'), ('DISABLED', 'غیرفعال')], default='AVAILABLE')),
            ]
        ),
        migrations.CreateModel(
            name='TakeawayProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pickup_number', models.CharField(max_length=32)),
                ('customer_name', models.CharField(max_length=120, blank=True)),
                ('customer_phone', models.CharField(max_length=20, blank=True)),
                ('notified_at', models.DateTimeField(null=True, blank=True)),
            ]
        ),
    ]
