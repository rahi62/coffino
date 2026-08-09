from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('businesses', '0001_initial'),
        ('printing', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='printerdevice', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='printers')),
        migrations.AddField(model_name='printtemplate', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='print_templates')),
        migrations.AddField(model_name='printjob', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='print_jobs')),
        migrations.AddField(model_name='printjob', name='printer', field=models.ForeignKey('printing.printerdevice', null=True, blank=True, on_delete=models.SET_NULL, related_name='jobs')),
        migrations.AddField(model_name='printjob', name='created_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
    ]
