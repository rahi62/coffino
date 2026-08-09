from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [('delivery', '0002_relations')]
    operations = [
        migrations.AlterUniqueTogether(name='deliveryzone', unique_together={('branch', 'code')}),
    ]
