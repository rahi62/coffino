from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('businesses', '0001_initial'),
        ('customers', '0001_initial'),
        ('dining', '0001_initial'),
        ('reservations', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='reservation', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='reservations')),
        migrations.AddField(model_name='reservation', name='table', field=models.ForeignKey('dining.table', null=True, blank=True, on_delete=models.SET_NULL, related_name='reservations')),
        migrations.AddField(model_name='reservation', name='customer', field=models.ForeignKey('customers.customer', null=True, blank=True, on_delete=models.SET_NULL, related_name='reservations')),
        migrations.AddField(model_name='reservation', name='created_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='reservation', name='seated_session', field=models.OneToOneField('dining.tablesession', null=True, blank=True, on_delete=models.SET_NULL, related_name='reservation')),
    ]
