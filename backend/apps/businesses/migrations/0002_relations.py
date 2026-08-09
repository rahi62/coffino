from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='branch', name='business', field=models.ForeignKey('businesses.business', on_delete=models.CASCADE, related_name='branches')),
        migrations.AddField(model_name='businessmodule', name='business', field=models.ForeignKey('businesses.business', on_delete=models.CASCADE, related_name='modules')),
    ]
