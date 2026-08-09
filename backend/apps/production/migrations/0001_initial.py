from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='ProductionFormula',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=160)),
                ('output_quantity', models.DecimalField(max_digits=14, decimal_places=3, default=1)),
                ('is_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='ProductionFormulaItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.DecimalField(max_digits=14, decimal_places=3)),
            ]
        ),
        migrations.CreateModel(
            name='ProductionBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('batch_number', models.CharField(max_length=80, blank=True)),
                ('multiplier', models.DecimalField(max_digits=14, decimal_places=3, default=1)),
                ('produced_quantity', models.DecimalField(max_digits=14, decimal_places=3, default=0)),
                ('total_cost', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('unit_cost', models.DecimalField(max_digits=14, decimal_places=2, default=0)),
                ('expires_at', models.DateTimeField(null=True, blank=True)),
                ('status', models.CharField(max_length=16, choices=[('DRAFT', 'پیش\u200cنویس'), ('POSTED', 'تولید شده'), ('CANCELLED', 'لغو')], default='DRAFT')),
                ('posted_at', models.DateTimeField(null=True, blank=True)),
                ('notes', models.TextField(blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='ProductionBatchIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.DecimalField(max_digits=14, decimal_places=3)),
                ('unit_cost', models.DecimalField(max_digits=14, decimal_places=2)),
                ('total_cost', models.DecimalField(max_digits=14, decimal_places=2)),
            ]
        ),
    ]
