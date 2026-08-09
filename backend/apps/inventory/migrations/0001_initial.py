from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=160)),
                ('unit', models.CharField(max_length=24, default='gram')),
                ('current_stock', models.DecimalField(max_digits=14, decimal_places=3, default=0)),
                ('minimum_stock', models.DecimalField(max_digits=14, decimal_places=3, default=0)),
                ('average_cost', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('last_purchase_cost', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('item_code', models.CharField(max_length=80, blank=True)),
                ('lot_tracked', models.BooleanField(default=False)),
                ('shelf_life_days', models.PositiveIntegerField(default=0)),
            ]
        ),
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('movement_type', models.CharField(max_length=24, choices=[('PURCHASE', 'خرید'), ('SALE_CONSUMPTION', 'مصرف فروش'), ('WASTE', 'ضایعات'), ('ADJUSTMENT', 'اصلاح'), ('RETURN', 'برگشت'), ('PRODUCTION', 'تولید'), ('TRANSFER_IN', 'انتقال ورودی'), ('TRANSFER_OUT', 'انتقال خروجی')])),
                ('quantity', models.DecimalField(max_digits=14, decimal_places=3)),
                ('reason', models.CharField(max_length=250, blank=True)),
                ('unit_cost', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('reference_type', models.CharField(max_length=40, blank=True)),
                ('reference_id', models.CharField(max_length=64, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='RecipeItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.DecimalField(max_digits=14, decimal_places=3)),
            ]
        ),
        migrations.CreateModel(
            name='WasteRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.DecimalField(max_digits=14, decimal_places=3)),
                ('unit_cost', models.DecimalField(max_digits=14, decimal_places=2)),
                ('total_cost', models.DecimalField(max_digits=14, decimal_places=2)),
                ('reason', models.CharField(max_length=160)),
                ('note', models.CharField(max_length=250, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='InventoryCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=160)),
                ('status', models.CharField(max_length=16, choices=[('DRAFT', 'پیش\u200cنویس'), ('POSTED', 'ثبت نهایی'), ('CANCELLED', 'لغو')], default='DRAFT')),
                ('posted_at', models.DateTimeField(null=True, blank=True)),
                ('notes', models.TextField(blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='InventoryCountLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('system_quantity', models.DecimalField(max_digits=14, decimal_places=3)),
                ('counted_quantity', models.DecimalField(max_digits=14, decimal_places=3)),
                ('variance', models.DecimalField(max_digits=14, decimal_places=3, default=0)),
                ('unit_cost_snapshot', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('variance_value', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
            ]
        ),
        migrations.CreateModel(
            name='StockTransfer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(max_length=16, choices=[('DRAFT', 'پیش\u200cنویس'), ('POSTED', 'ثبت نهایی'), ('CANCELLED', 'لغو')], default='DRAFT')),
                ('posted_at', models.DateTimeField(null=True, blank=True)),
                ('reference', models.CharField(max_length=80, blank=True)),
                ('notes', models.TextField(blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='StockTransferLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.DecimalField(max_digits=14, decimal_places=3)),
                ('unit_cost_snapshot', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
            ]
        ),
        migrations.CreateModel(
            name='InventoryLot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('lot_number', models.CharField(max_length=100)),
                ('received_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(null=True, blank=True)),
                ('quantity_received', models.DecimalField(max_digits=14, decimal_places=3)),
                ('quantity_remaining', models.DecimalField(max_digits=14, decimal_places=3)),
                ('unit_cost', models.DecimalField(max_digits=14, decimal_places=2)),
                ('source_type', models.CharField(max_length=40, blank=True)),
                ('source_id', models.CharField(max_length=64, blank=True)),
                ('is_blocked', models.BooleanField(default=False)),
                ('notes', models.CharField(max_length=250, blank=True)),
            ],
            options={'ordering': ['expires_at', 'received_at', 'id']}
        ),
        migrations.CreateModel(
            name='LotInventoryCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=160)),
                ('status', models.CharField(max_length=16, choices=[('DRAFT', 'پیش\u200cنویس'), ('POSTED', 'ثبت نهایی'), ('CANCELLED', 'لغو')], default='DRAFT')),
                ('posted_at', models.DateTimeField(null=True, blank=True)),
                ('notes', models.TextField(blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='LotInventoryCountLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('system_quantity', models.DecimalField(max_digits=14, decimal_places=3)),
                ('counted_quantity', models.DecimalField(max_digits=14, decimal_places=3)),
                ('variance', models.DecimalField(max_digits=14, decimal_places=3, default=0)),
                ('variance_value', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
            ]
        ),
    ]
