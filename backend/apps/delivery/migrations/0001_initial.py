from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='DeliveryZone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=140)),
                ('code', models.CharField(max_length=60)),
                ('delivery_fee', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('min_order_amount', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('free_delivery_above', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('estimated_minutes', models.PositiveIntegerField(default=35)),
                ('is_active', models.BooleanField(default=True)),
            ]
        ),
        migrations.CreateModel(
            name='DeliveryAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=80, blank=True)),
                ('recipient_name', models.CharField(max_length=140)),
                ('phone', models.CharField(max_length=24)),
                ('address', models.TextField()),
                ('postal_code', models.CharField(max_length=20, blank=True)),
                ('latitude', models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)),
                ('longitude', models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)),
                ('notes', models.CharField(max_length=250, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='CourierProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=140)),
                ('phone', models.CharField(max_length=24, blank=True)),
                ('vehicle', models.CharField(max_length=80, blank=True)),
                ('plate', models.CharField(max_length=40, blank=True)),
                ('status', models.CharField(max_length=16, choices=[('AVAILABLE', 'آماده'), ('BUSY', 'مشغول'), ('OFFLINE', 'آفلاین')], default='AVAILABLE')),
                ('is_active', models.BooleanField(default=True)),
            ]
        ),
        migrations.CreateModel(
            name='DeliveryAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('delivery_fee', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('status', models.CharField(max_length=20, choices=[('WAITING', 'در انتظار پیک'), ('ASSIGNED', 'اختصاص داده شد'), ('PICKED_UP', 'تحویل از مجموعه'), ('DELIVERED', 'تحویل مشتری'), ('FAILED', 'ناموفق'), ('CANCELLED', 'لغو')], default='WAITING')),
                ('assigned_at', models.DateTimeField(null=True, blank=True)),
                ('picked_up_at', models.DateTimeField(null=True, blank=True)),
                ('delivered_at', models.DateTimeField(null=True, blank=True)),
                ('proof_note', models.CharField(max_length=250, blank=True)),
            ]
        ),
    ]
