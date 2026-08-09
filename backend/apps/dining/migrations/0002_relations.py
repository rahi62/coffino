from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('businesses', '0001_initial'),
        ('dining', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='hall', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='halls')),
        migrations.AddField(model_name='table', name='hall', field=models.ForeignKey('dining.hall', on_delete=models.CASCADE, related_name='tables')),
        migrations.AddField(model_name='tablesession', name='table', field=models.ForeignKey('dining.table', on_delete=models.CASCADE, related_name='sessions')),
        migrations.AddField(model_name='tablesession', name='opened_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='tabletransferlog', name='session', field=models.ForeignKey('dining.tablesession', on_delete=models.PROTECT, related_name='transfer_logs')),
        migrations.AddField(model_name='tabletransferlog', name='from_table', field=models.ForeignKey('dining.table', on_delete=models.PROTECT, related_name='transfers_out')),
        migrations.AddField(model_name='tabletransferlog', name='to_table', field=models.ForeignKey('dining.table', on_delete=models.PROTECT, related_name='transfers_in')),
        migrations.AddField(model_name='tabletransferlog', name='transferred_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
    ]
