from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
        ('suppliers', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='supplier', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='suppliers')),
    ]
