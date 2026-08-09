from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer_name', models.CharField(max_length=160)),
                ('phone', models.CharField(max_length=24, blank=True)),
                ('party_size', models.PositiveIntegerField(default=2)),
                ('reserved_for', models.DateTimeField()),
                ('duration_minutes', models.PositiveIntegerField(default=90)),
                ('status', models.CharField(max_length=16, choices=[('PENDING', 'در انتظار'), ('CONFIRMED', 'تأیید'), ('SEATED', 'مستقر'), ('COMPLETED', 'تکمیل'), ('CANCELLED', 'لغو'), ('NO_SHOW', 'عدم مراجعه')], default='PENDING')),
                ('source', models.CharField(max_length=24, default='STAFF')),
                ('notes', models.TextField(blank=True)),
            ],
            options={'ordering': ['reserved_for']}
        ),
    ]
