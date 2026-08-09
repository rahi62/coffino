from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='PurchaseInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invoice_number', models.CharField(max_length=80, blank=True)),
                ('invoice_date', models.DateField()),
                ('status', models.CharField(max_length=16, choices=[('DRAFT', 'پیش نویس'), ('POSTED', 'ثبت شده'), ('CANCELLED', 'لغو')], default='DRAFT')),
                ('total_amount', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('paid_amount', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('notes', models.TextField(blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='PurchaseItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.DecimalField(max_digits=14, decimal_places=3)),
                ('unit_cost', models.DecimalField(max_digits=14, decimal_places=2)),
                ('line_total', models.DecimalField(max_digits=14, decimal_places=0)),
                ('lot_number', models.CharField(max_length=100, blank=True)),
                ('expires_at', models.DateTimeField(null=True, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='SupplierPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('amount', models.DecimalField(max_digits=14, decimal_places=0)),
                ('method', models.CharField(max_length=24, default='CASH')),
                ('reference', models.CharField(max_length=120, blank=True)),
                ('paid_at', models.DateTimeField(auto_now_add=True)),
            ]
        ),
    ]
