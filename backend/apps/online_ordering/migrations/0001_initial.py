from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='OnlineMenuSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('public_slug', models.SlugField(max_length=100, unique=True)),
                ('is_enabled', models.BooleanField(default=False)),
                ('accepting_orders', models.BooleanField(default=False)),
                ('payment_mode', models.CharField(max_length=24, choices=[('PAY_AT_COUNTER', 'پرداخت صندوق'), ('ONLINE', 'آنلاین')], default='PAY_AT_COUNTER')),
                ('allow_takeaway', models.BooleanField(default=True)),
                ('allow_pickup', models.BooleanField(default=True)),
                ('allow_dine_in_qr', models.BooleanField(default=True)),
                ('allow_delivery', models.BooleanField(default=False)),
                ('public_base_url', models.URLField(default='http://127.0.0.1:3000')),
                ('estimated_minutes', models.PositiveIntegerField(default=20)),
                ('min_order_amount', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('welcome_text', models.CharField(max_length=250, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='TableQrToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('token', models.UUIDField(default=uuid.uuid4, unique=True, editable=False)),
                ('is_active', models.BooleanField(default=True)),
            ]
        ),
        migrations.CreateModel(
            name='OnlineOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('access_token', models.UUIDField(default=uuid.uuid4, unique=True, editable=False)),
                ('source', models.CharField(max_length=20, default='WEB')),
                ('status', models.CharField(max_length=16, choices=[('PAYMENT_PENDING', 'در انتظار پرداخت'), ('RECEIVED', 'دریافت'), ('ACCEPTED', 'پذیرفته'), ('REJECTED', 'رد'), ('READY', 'آماده'), ('COMPLETED', 'تکمیل')], default='RECEIVED')),
                ('customer_name', models.CharField(max_length=160, blank=True)),
                ('customer_phone', models.CharField(max_length=24, blank=True)),
                ('payment_mode', models.CharField(max_length=24)),
                ('estimated_minutes', models.PositiveIntegerField(default=20)),
            ]
        ),
    ]
