from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0003_constraints'),
        ('audit', '0003_constraints'),
    ]

    operations = [
        migrations.AddField(
            model_name='auditlog',
            name='business',
            field=models.ForeignKey(
                null=True,blank=True,on_delete=django.db.models.deletion.SET_NULL,
                related_name='audit_logs',to='businesses.business'
            ),
        ),
    ]

