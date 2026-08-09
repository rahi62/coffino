from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [('inventory', '0002_relations')]
    operations = [
        migrations.AlterUniqueTogether(name='inventorycountline', unique_together={('count', 'item')}),
        migrations.AlterUniqueTogether(name='inventorylot', unique_together={('item', 'lot_number')}),
        migrations.AlterUniqueTogether(name='lotinventorycountline', unique_together={('count', 'lot')}),
    ]
