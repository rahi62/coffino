from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='PrinterDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120)),
                ('system_name', models.CharField(max_length=250, blank=True)),
                ('kind', models.CharField(max_length=16, choices=[('RECEIPT', 'فیش'), ('KITCHEN', 'آشپزخانه'), ('BAR', 'بار'), ('GENERAL', 'عمومی')], default='RECEIPT')),
                ('paper_width', models.PositiveIntegerField(default=80)),
                ('is_active', models.BooleanField(default=True)),
            ]
        ),
        migrations.CreateModel(
            name='PrintTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120)),
                ('document_type', models.CharField(max_length=16, choices=[('RECEIPT', 'رسید مشتری'), ('KITCHEN', 'تیکت آشپزخانه'), ('BAR', 'تیکت بار')])),
                ('header', models.TextField(blank=True)),
                ('footer', models.TextField(blank=True)),
                ('show_tax', models.BooleanField(default=True)),
                ('show_service_charge', models.BooleanField(default=True)),
                ('show_customer', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
            ]
        ),
        migrations.CreateModel(
            name='PrintJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document_type', models.CharField(max_length=16)),
                ('entity_type', models.CharField(max_length=40, blank=True)),
                ('entity_id', models.CharField(max_length=64, blank=True)),
                ('payload', models.JSONField(default=dict)),
                ('status', models.CharField(max_length=16, choices=[('PENDING', 'در انتظار'), ('PRINTED', 'چاپ شده'), ('FAILED', 'خطا')], default='PENDING')),
                ('error', models.TextField(blank=True)),
                ('printed_at', models.DateTimeField(null=True, blank=True)),
            ]
        ),
    ]
