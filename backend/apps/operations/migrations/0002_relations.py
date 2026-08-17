from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies=[
        ('businesses','0003_constraints'),
        ('operations','0001_initial'),
    ]
    operations=[
        migrations.AddField(
            model_name='deviceinstallation',name='business',
            field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='device_installations',to='businesses.business'),
        ),
        migrations.AddField(
            model_name='deviceinstallation',name='branch',
            field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='device_installations',to='businesses.branch'),
        ),
    ]
