from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [('accounts', '0002_relations')]
    operations = [
        migrations.AddConstraint(model_name='user', constraint=models.CheckConstraint(condition=Q(is_superuser=True) | Q(business__isnull=False) & (Q(role__in=['OWNER', 'MANAGER']) | Q(branch__isnull=False)), name='user_tenant_scope_required')),
    ]
