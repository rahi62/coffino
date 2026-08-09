from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='StaffSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('work_date', models.DateField()),
                ('starts_at', models.TimeField()),
                ('ends_at', models.TimeField()),
                ('notes', models.CharField(max_length=250, blank=True)),
            ]
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('clock_in', models.DateTimeField()),
                ('clock_out', models.DateTimeField(null=True, blank=True)),
                ('source', models.CharField(max_length=30, default='APP')),
                ('note', models.CharField(max_length=250, blank=True)),
            ]
        ),
    ]
