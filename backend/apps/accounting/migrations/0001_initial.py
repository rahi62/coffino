from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='ExpenseCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120)),
            ]
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=160)),
                ('amount', models.DecimalField(max_digits=14, decimal_places=0)),
                ('payment_method', models.CharField(max_length=24, default='CASH')),
                ('occurred_at', models.DateTimeField()),
                ('notes', models.TextField(blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='FixedOverhead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=160)),
                ('amount', models.DecimalField(max_digits=14, decimal_places=0)),
                ('frequency', models.CharField(max_length=16, choices=[('DAILY', 'روزانه'), ('MONTHLY', 'ماهانه'), ('YEARLY', 'سالانه')], default='MONTHLY')),
                ('is_active', models.BooleanField(default=True)),
            ]
        ),
        migrations.CreateModel(
            name='FiscalSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tax_rate', models.DecimalField(max_digits=6, decimal_places=3, default=0)),
                ('service_charge_rate', models.DecimalField(max_digits=6, decimal_places=3, default=0)),
                ('prices_include_tax', models.BooleanField(default=False)),
                ('service_charge_order_types', models.JSONField(default=list, blank=True)),
                ('tax_enabled', models.BooleanField(default=False)),
                ('service_charge_enabled', models.BooleanField(default=False)),
                ('service_charge_is_revenue', models.BooleanField(default=True)),
                ('delivery_fee_taxable', models.BooleanField(default=False)),
                ('receipt_tax_label', models.CharField(max_length=80, default='مالیات')),
                ('receipt_service_label', models.CharField(max_length=80, default='حق سرویس')),
            ]
        ),
    ]
