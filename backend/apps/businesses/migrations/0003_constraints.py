from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [('businesses', '0002_relations')]
    operations = [
        migrations.AlterUniqueTogether(name='businessmodule', unique_together={('business', 'key')}),
    ]
