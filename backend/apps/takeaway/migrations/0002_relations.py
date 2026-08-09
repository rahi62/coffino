from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
        ('orders', '0001_initial'),
        ('takeaway', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='pagerdevice', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='pagers')),
        migrations.AddField(model_name='takeawayprofile', name='order', field=models.OneToOneField('orders.order', on_delete=models.CASCADE, related_name='takeaway_profile')),
        migrations.AddField(model_name='takeawayprofile', name='pager', field=models.ForeignKey('takeaway.pagerdevice', null=True, blank=True, on_delete=models.SET_NULL, related_name='assignments')),
    ]
