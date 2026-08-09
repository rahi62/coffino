from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='GiftCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code_hash', models.CharField(max_length=64, db_index=True)),
                ('code_last4', models.CharField(max_length=4)),
                ('initial_balance', models.DecimalField(max_digits=14, decimal_places=0)),
                ('balance', models.DecimalField(max_digits=14, decimal_places=0)),
                ('expires_at', models.DateTimeField(null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('purchaser_name', models.CharField(max_length=140, blank=True)),
                ('recipient_name', models.CharField(max_length=140, blank=True)),
                ('note', models.CharField(max_length=250, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='GiftCardTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('transaction_type', models.CharField(max_length=16, choices=[('ISSUE', 'صدور'), ('DEBIT', 'مصرف'), ('REFUND', 'برگشت'), ('ADJUST', 'اصلاح')])),
                ('amount', models.DecimalField(max_digits=14, decimal_places=0)),
                ('balance_after', models.DecimalField(max_digits=14, decimal_places=0)),
                ('reference', models.CharField(max_length=100, blank=True)),
            ]
        ),
    ]
