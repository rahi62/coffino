from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('businesses', '0001_initial'),
        ('customers', '0001_initial'),
        ('delivery', '0001_initial'),
        ('orders', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='deliveryzone', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='delivery_zones')),
        migrations.AddField(model_name='deliveryaddress', name='customer', field=models.ForeignKey('customers.customer', null=True, blank=True, on_delete=models.CASCADE, related_name='delivery_addresses')),
        migrations.AddField(model_name='deliveryaddress', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='delivery_addresses')),
        migrations.AddField(model_name='deliveryaddress', name='zone', field=models.ForeignKey('delivery.deliveryzone', null=True, blank=True, on_delete=models.SET_NULL, related_name='addresses')),
        migrations.AddField(model_name='courierprofile', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='couriers')),
        migrations.AddField(model_name='courierprofile', name='user', field=models.OneToOneField('accounts.user', null=True, blank=True, on_delete=models.SET_NULL, related_name='courier_profile')),
        migrations.AddField(model_name='deliveryassignment', name='order', field=models.OneToOneField('orders.order', on_delete=models.CASCADE, related_name='delivery_assignment')),
        migrations.AddField(model_name='deliveryassignment', name='address', field=models.ForeignKey('delivery.deliveryaddress', on_delete=models.PROTECT, related_name='assignments')),
        migrations.AddField(model_name='deliveryassignment', name='courier', field=models.ForeignKey('delivery.courierprofile', null=True, blank=True, on_delete=models.SET_NULL, related_name='assignments')),
        migrations.AddField(model_name='deliveryassignment', name='zone', field=models.ForeignKey('delivery.deliveryzone', null=True, blank=True, on_delete=models.SET_NULL)),
    ]
