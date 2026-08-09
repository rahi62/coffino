from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
        ('customers', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='customer', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='customers')),
    ]
