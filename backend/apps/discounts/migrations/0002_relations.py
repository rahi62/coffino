from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
        ('catalog', '0001_initial'),
        ('discounts', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='discountrule', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='discount_rules')),
        migrations.AddField(model_name='discountrule', name='category', field=models.ForeignKey('catalog.category', null=True, blank=True, on_delete=models.CASCADE)),
        migrations.AddField(model_name='discountrule', name='product', field=models.ForeignKey('catalog.product', null=True, blank=True, on_delete=models.CASCADE)),
    ]
