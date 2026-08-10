from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('takeaway', '0003_constraints')]

    operations = [
        migrations.AddField(
            model_name='takeawayprofile',
            name='ready_notification_method',
            field=models.CharField(
                choices=[('SMS', 'پیامک'), ('PAGER', 'پیجر'), ('NONE', 'بدون اعلان')],
                default='SMS', max_length=12,
            ),
        ),
    ]
