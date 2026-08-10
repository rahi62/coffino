from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('inventory', '0003_constraints')]

    operations = [
        migrations.AddField(
            model_name='inventoryitem',
            name='category',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AddField(
            model_name='inventoryitem',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
