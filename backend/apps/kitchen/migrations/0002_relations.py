from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
        ('kitchen', '0001_initial'),
        ('orders', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='preparationstation', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='stations')),
        migrations.AddField(model_name='kitchenticket', name='order', field=models.ForeignKey('orders.order', on_delete=models.CASCADE, related_name='kitchen_tickets')),
        migrations.AddField(model_name='kitchenticket', name='station', field=models.ForeignKey('kitchen.preparationstation', on_delete=models.CASCADE, related_name='tickets')),
    ]
