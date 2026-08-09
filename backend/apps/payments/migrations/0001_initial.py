from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('amount', models.DecimalField(max_digits=14, decimal_places=0)),
                ('method', models.CharField(max_length=16, choices=[('CASH', 'نقدی'), ('POS', 'کارتخوان'), ('ONLINE', 'آنلاین'), ('CREDIT', 'اعتباری'), ('WALLET', 'کیف پول'), ('GIFT_CARD', 'کارت هدیه')])),
                ('status', models.CharField(max_length=24, choices=[('PENDING', 'در انتظار'), ('SUCCEEDED', 'موفق'), ('FAILED', 'ناموفق'), ('PARTIALLY_REFUNDED', 'بخشی برگشت'), ('REFUNDED', 'برگشت کامل')], default='SUCCEEDED')),
                ('reference_number', models.CharField(max_length=120, blank=True)),
                ('payer_label', models.CharField(max_length=80, blank=True)),
                ('tendered_amount', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('change_amount', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
            ]
        ),
        migrations.CreateModel(
            name='Refund',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('amount', models.DecimalField(max_digits=14, decimal_places=0)),
                ('reason', models.CharField(max_length=250)),
                ('method', models.CharField(max_length=16, choices=[('CASH', 'نقدی'), ('POS', 'کارتخوان'), ('ONLINE', 'آنلاین'), ('CREDIT', 'اعتباری'), ('WALLET', 'کیف پول'), ('GIFT_CARD', 'کارت هدیه')])),
                ('reference_number', models.CharField(max_length=120, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='BillSplit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('label', models.CharField(max_length=80)),
                ('items_subtotal', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('discount_share', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('service_charge_share', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('tax_share', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('total', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('status', models.CharField(max_length=16, choices=[('OPEN', 'باز'), ('PARTIAL', 'بخشی'), ('PAID', 'پرداخت'), ('CANCELLED', 'لغو')], default='OPEN')),
            ]
        ),
        migrations.CreateModel(
            name='BillSplitLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.DecimalField(max_digits=10, decimal_places=3)),
                ('subtotal_share', models.DecimalField(max_digits=14, decimal_places=0)),
            ]
        ),
    ]
