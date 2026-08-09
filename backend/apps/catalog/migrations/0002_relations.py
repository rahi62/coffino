from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
        ('catalog', '0001_initial'),
        ('inventory', '0001_initial'),
        ('kitchen', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='category', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='categories')),
        migrations.AddField(model_name='product', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='products')),
        migrations.AddField(model_name='product', name='category', field=models.ForeignKey('catalog.category', null=True, blank=True, on_delete=models.SET_NULL, related_name='products')),
        migrations.AddField(model_name='product', name='preparation_station', field=models.ForeignKey('kitchen.preparationstation', null=True, blank=True, on_delete=models.SET_NULL, related_name='products')),
        migrations.AddField(model_name='product', name='stock_item', field=models.ForeignKey('inventory.inventoryitem', null=True, blank=True, on_delete=models.SET_NULL, related_name='sale_products')),
    ]
