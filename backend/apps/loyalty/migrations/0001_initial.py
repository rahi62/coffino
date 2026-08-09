from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='LoyaltyProgram',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('amount_per_point', models.DecimalField(max_digits=14, decimal_places=0, default=100000)),
                ('point_wallet_value', models.DecimalField(max_digits=14, decimal_places=0, default=10000)),
                ('min_redeem_points', models.PositiveIntegerField(default=10)),
                ('welcome_points', models.PositiveIntegerField(default=0)),
            ]
        ),
        migrations.CreateModel(
            name='CustomerLoyaltyAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('points_balance', models.IntegerField(default=0)),
                ('lifetime_points', models.PositiveIntegerField(default=0)),
                ('tier', models.CharField(max_length=40, default='STANDARD')),
            ]
        ),
        migrations.CreateModel(
            name='LoyaltyLedger',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('entry_type', models.CharField(max_length=16, choices=[('EARN', 'کسب'), ('REDEEM', 'مصرف'), ('ADJUST', 'اصلاح'), ('EXPIRE', 'انقضا')])),
                ('points', models.IntegerField()),
                ('balance_after', models.IntegerField()),
                ('note', models.CharField(max_length=250, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='WalletAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('balance', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
            ]
        ),
        migrations.CreateModel(
            name='WalletTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('transaction_type', models.CharField(max_length=16, choices=[('CREDIT', 'واریز'), ('DEBIT', 'برداشت'), ('REFUND', 'برگشت'), ('ADJUST', 'اصلاح'), ('LOYALTY', 'تبدیل امتیاز')])),
                ('amount', models.DecimalField(max_digits=14, decimal_places=0)),
                ('balance_after', models.DecimalField(max_digits=14, decimal_places=0)),
                ('reference', models.CharField(max_length=100, blank=True)),
                ('note', models.CharField(max_length=250, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='LoyaltyTier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=80)),
                ('code', models.CharField(max_length=40)),
                ('min_lifetime_points', models.PositiveIntegerField(default=0)),
                ('points_multiplier', models.DecimalField(max_digits=6, decimal_places=2, default=1)),
                ('priority', models.PositiveIntegerField(default=100)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['min_lifetime_points', 'priority']}
        ),
        migrations.CreateModel(
            name='LoyaltyCampaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120)),
                ('points_multiplier', models.DecimalField(max_digits=6, decimal_places=2, default=1)),
                ('bonus_points', models.PositiveIntegerField(default=0)),
                ('starts_at', models.DateTimeField()),
                ('ends_at', models.DateTimeField()),
                ('order_types', models.JSONField(default=list, blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ]
        ),
    ]
