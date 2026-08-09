from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order_number', models.PositiveIntegerField()),
                ('order_type', models.CharField(max_length=24, choices=[('DINE_IN', 'داخل سالن'), ('TAKEAWAY', 'بیرون\u200cبر'), ('PICKUP', 'تحویل حضوری'), ('DELIVERY', 'ارسال'), ('DRIVE_THROUGH', 'دریافت خودرو'), ('CATERING', 'کترینگ')])),
                ('status', models.CharField(max_length=24, choices=[('DRAFT', 'پیش\u200cنویس'), ('CONFIRMED', 'تأیید شده'), ('IN_PROGRESS', 'در حال آماده\u200cسازی'), ('READY', 'آماده'), ('COMPLETED', 'تکمیل'), ('CANCELLED', 'لغو')], default='DRAFT')),
                ('payment_status', models.CharField(max_length=24, choices=[('UNPAID', 'پرداخت نشده'), ('PARTIALLY_PAID', 'بخشی/تسویه ناقص'), ('PAID', 'پرداخت شده'), ('PARTIALLY_REFUNDED', 'بخشی برگشت'), ('REFUNDED', 'برگشت کامل')], default='UNPAID')),
                ('subtotal', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('discount_total', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('discount_reason', models.CharField(max_length=250, blank=True)),
                ('tax_total', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('service_charge_total', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('delivery_fee_total', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('grand_total', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('notes', models.TextField(blank=True)),
                ('idempotency_key', models.CharField(max_length=100, null=True, blank=True)),
                ('idempotency_fingerprint', models.CharField(max_length=64, blank=True)),
            ],
            options={'ordering': ['-created_at']}
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product_name', models.CharField(max_length=160)),
                ('quantity', models.DecimalField(max_digits=10, decimal_places=3, default=1)),
                ('unit_price', models.DecimalField(max_digits=14, decimal_places=0)),
                ('unit_cost_snapshot', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('line_total', models.DecimalField(max_digits=14, decimal_places=0)),
                ('status', models.CharField(max_length=20, choices=[('NEW', 'جدید'), ('PREPARING', 'در حال آماده\u200cسازی'), ('READY', 'آماده'), ('HANDED_OVER', 'تحویل')], default='NEW')),
                ('notes', models.CharField(max_length=250, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='ApprovalRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('request_type', models.CharField(max_length=20, choices=[('DISCOUNT', 'تخفیف'), ('VOID', 'لغو سفارش')])),
                ('status', models.CharField(max_length=16, choices=[('PENDING', 'در انتظار'), ('APPROVED', 'تأیید'), ('REJECTED', 'رد')], default='PENDING')),
                ('amount', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('percent', models.DecimalField(max_digits=6, decimal_places=2, default=0)),
                ('reason', models.CharField(max_length=250)),
                ('decided_at', models.DateTimeField(null=True, blank=True)),
            ]
        ),
    ]
