from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
        ('customers', '0001_initial'),
        ('notifications', '0001_initial'),
        ('orders', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='smsproviderconfig', name='branch', field=models.OneToOneField('businesses.branch', on_delete=models.CASCADE, related_name='sms_provider')),
        migrations.AddField(model_name='notification', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='notifications')),
        migrations.AddField(model_name='notification', name='customer', field=models.ForeignKey('customers.customer', null=True, blank=True, on_delete=models.SET_NULL, related_name='notifications')),
        migrations.AddField(model_name='notification', name='order', field=models.ForeignKey('orders.order', null=True, blank=True, on_delete=models.SET_NULL, related_name='notifications')),
        migrations.AddField(model_name='pushproviderconfig', name='branch', field=models.OneToOneField('businesses.branch', on_delete=models.CASCADE, related_name='push_provider')),
        migrations.AddField(model_name='pushsubscription', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='push_subscriptions')),
        migrations.AddField(model_name='pushsubscription', name='customer', field=models.ForeignKey('customers.customer', null=True, blank=True, on_delete=models.CASCADE, related_name='push_subscriptions')),
        migrations.AddField(model_name='pushsubscription', name='order', field=models.ForeignKey('orders.order', null=True, blank=True, on_delete=models.CASCADE, related_name='push_subscriptions')),
    ]
