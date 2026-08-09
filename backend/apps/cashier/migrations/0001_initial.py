from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='CashRegister',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120)),
                ('is_active', models.BooleanField(default=True)),
            ]
        ),
        migrations.CreateModel(
            name='CashShift',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('opening_balance', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('expected_cash', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('closing_balance', models.DecimalField(max_digits=14, decimal_places=0, null=True, blank=True)),
                ('difference', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('is_open', models.BooleanField(default=True)),
                ('opened_at', models.DateTimeField(auto_now_add=True)),
                ('closed_at', models.DateTimeField(null=True, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='CashMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('movement_type', models.CharField(max_length=24, choices=[('SALE', 'فروش نقدی'), ('REFUND', 'برگشت وجه نقدی'), ('CASH_IN', 'ورود نقد'), ('CASH_OUT', 'خروج نقد'), ('EXPENSE', 'هزینه نقدی'), ('SUPPLIER_PAYMENT', 'پرداخت نقدی تامین\u200cکننده'), ('ADJUSTMENT', 'اصلاح')])),
                ('amount', models.DecimalField(max_digits=14, decimal_places=0)),
                ('note', models.CharField(max_length=250, blank=True)),
                ('reference_type', models.CharField(max_length=40, blank=True)),
                ('reference_id', models.CharField(max_length=64, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='DailyClosing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business_date', models.DateField()),
                ('gross_sales', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('refunds', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('net_sales', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('cash_sales', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('pos_sales', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('expenses', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('expected_cash', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('counted_cash', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('cash_difference', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('closed_at', models.DateTimeField(auto_now_add=True)),
                ('snapshot', models.JSONField(default=dict, blank=True)),
            ],
            options={'ordering': ['-business_date']}
        ),
    ]
