from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [('loyalty', '0002_relations')]
    operations = [
        migrations.AddConstraint(model_name='loyaltyledger', constraint=models.UniqueConstraint(fields=['account', 'order', 'entry_type'], condition=models.Q(order__isnull=False), name='uniq_loyalty_order_type')),
        migrations.AlterUniqueTogether(name='loyaltytier', unique_together={('branch', 'code')}),
    ]
