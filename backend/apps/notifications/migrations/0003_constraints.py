from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [('notifications', '0002_relations')]
    operations = [
        migrations.AddConstraint(model_name='notification', constraint=models.UniqueConstraint(fields=['branch', 'dedupe_key'], condition=~models.Q(dedupe_key=''), name='uniq_notification_dedupe_branch')),
        migrations.AddConstraint(model_name='pushsubscription', constraint=models.UniqueConstraint(fields=['branch', 'endpoint'], name='uniq_push_endpoint_branch')),
    ]
