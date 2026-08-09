from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('audit', '0001_initial'),
        ('businesses', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='auditlog', name='branch', field=models.ForeignKey('businesses.branch', null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs')),
        migrations.AddField(model_name='auditlog', name='actor', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs')),
    ]
