from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [('orders', '0002_relations')]
    operations = [
        migrations.AlterUniqueTogether(name='order', unique_together={('branch', 'order_number')}),
        migrations.AddConstraint(model_name='order', constraint=models.UniqueConstraint(fields=['branch', 'idempotency_key'], condition=models.Q(idempotency_key__isnull=False), name='uniq_order_idempotency_per_branch')),
    ]
