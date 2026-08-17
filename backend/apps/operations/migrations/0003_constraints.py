from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies=[('operations','0002_relations')]
    operations=[
        migrations.AddConstraint(
            model_name='deviceinstallation',
            constraint=models.UniqueConstraint(fields=('license_id','machine_hash'),name='ops_device_license_machine_unique'),
        ),
        migrations.AddConstraint(
            model_name='releasepolicy',
            constraint=models.CheckConstraint(condition=models.Q(('rollout_percent__gte',0),('rollout_percent__lte',100)),name='ops_release_rollout_percent_range'),
        ),
    ]
