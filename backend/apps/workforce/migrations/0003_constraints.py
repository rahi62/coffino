from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [('workforce', '0002_relations')]
    operations = [
        migrations.AlterUniqueTogether(name='staffschedule', unique_together={('user', 'work_date', 'starts_at')}),
    ]
