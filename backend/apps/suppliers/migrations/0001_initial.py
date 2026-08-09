from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=160)),
                ('phone', models.CharField(max_length=32, blank=True)),
                ('address', models.TextField(blank=True)),
                ('opening_balance', models.DecimalField(max_digits=14, decimal_places=0, default=0)),
                ('is_active', models.BooleanField(default=True)),
            ]
        ),
    ]
