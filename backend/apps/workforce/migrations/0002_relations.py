from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('businesses', '0001_initial'),
        ('workforce', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='staffschedule', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='staff_schedules')),
        migrations.AddField(model_name='staffschedule', name='user', field=models.ForeignKey('accounts.user', on_delete=models.CASCADE, related_name='staff_schedules')),
        migrations.AddField(model_name='attendance', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='attendance')),
        migrations.AddField(model_name='attendance', name='user', field=models.ForeignKey('accounts.user', on_delete=models.CASCADE, related_name='attendance')),
    ]
