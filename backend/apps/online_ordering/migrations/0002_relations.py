from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
        ('delivery', '0001_initial'),
        ('dining', '0001_initial'),
        ('online_ordering', '0001_initial'),
        ('orders', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='onlinemenusettings', name='branch', field=models.OneToOneField('businesses.branch', on_delete=models.CASCADE, related_name='online_menu_settings')),
        migrations.AddField(model_name='tableqrtoken', name='table', field=models.OneToOneField('dining.table', on_delete=models.CASCADE, related_name='qr_token')),
        migrations.AddField(model_name='onlineorder', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='online_orders')),
        migrations.AddField(model_name='onlineorder', name='order', field=models.OneToOneField('orders.order', on_delete=models.CASCADE, related_name='online_order')),
        migrations.AddField(model_name='onlineorder', name='table_token', field=models.ForeignKey('online_ordering.tableqrtoken', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='onlineorder', name='delivery_address', field=models.ForeignKey('delivery.deliveryaddress', null=True, blank=True, on_delete=models.SET_NULL, related_name='online_orders')),
    ]
