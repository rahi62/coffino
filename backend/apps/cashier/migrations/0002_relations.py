from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('businesses', '0001_initial'),
        ('cashier', '0001_initial'),
        ('payments', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='cashregister', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='cash_registers')),
        migrations.AddField(model_name='cashshift', name='register', field=models.ForeignKey('cashier.cashregister', on_delete=models.CASCADE, related_name='shifts')),
        migrations.AddField(model_name='cashshift', name='cashier', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='cashmovement', name='shift', field=models.ForeignKey('cashier.cashshift', on_delete=models.CASCADE, related_name='movements')),
        migrations.AddField(model_name='cashmovement', name='payment', field=models.ForeignKey('payments.payment', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='cashmovement', name='created_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='dailyclosing', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='daily_closings')),
        migrations.AddField(model_name='dailyclosing', name='closed_by', field=models.ForeignKey('accounts.user', null=True, on_delete=models.SET_NULL)),
    ]
