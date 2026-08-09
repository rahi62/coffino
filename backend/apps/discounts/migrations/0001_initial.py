from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='DiscountRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=140)),
                ('code', models.CharField(max_length=40, blank=True)),
                ('trigger', models.CharField(max_length=12, choices=[('AUTO', 'خودکار'), ('CODE', 'کد تخفیف')], default='AUTO')),
                ('scope', models.CharField(max_length=16, choices=[('ORDER', 'کل سفارش'), ('CATEGORY', 'دسته'), ('PRODUCT', 'محصول')], default='ORDER')),
                ('kind', models.CharField(max_length=12, choices=[('PERCENT', 'درصدی'), ('FIXED', 'مبلغ ثابت')], default='PERCENT')),
                ('value', models.DecimalField(max_digits=14, decimal_places=2)),
                ('min_order_amount', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('max_discount', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('starts_at', models.DateTimeField(null=True, blank=True)),
                ('ends_at', models.DateTimeField(null=True, blank=True)),
                ('weekdays', models.JSONField(default=list, blank=True, help_text='0=Monday ... 6=Sunday; empty means all')),
                ('priority', models.IntegerField(default=100)),
                ('is_active', models.BooleanField(default=True)),
                ('requires_manager', models.BooleanField(default=False)),
            ]
        ),
    ]
