from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('businesses', '0001_initial'),
        ('customers', '0001_initial'),
        ('loyalty', '0001_initial'),
        ('orders', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='loyaltyprogram', name='branch', field=models.OneToOneField('businesses.branch', on_delete=models.CASCADE, related_name='loyalty_program')),
        migrations.AddField(model_name='customerloyaltyaccount', name='customer', field=models.OneToOneField('customers.customer', on_delete=models.CASCADE, related_name='loyalty_account')),
        migrations.AddField(model_name='loyaltyledger', name='account', field=models.ForeignKey('loyalty.customerloyaltyaccount', on_delete=models.CASCADE, related_name='ledger')),
        migrations.AddField(model_name='loyaltyledger', name='order', field=models.ForeignKey('orders.order', null=True, blank=True, on_delete=models.SET_NULL, related_name='loyalty_entries')),
        migrations.AddField(model_name='walletaccount', name='customer', field=models.OneToOneField('customers.customer', on_delete=models.CASCADE, related_name='wallet')),
        migrations.AddField(model_name='wallettransaction', name='wallet', field=models.ForeignKey('loyalty.walletaccount', on_delete=models.CASCADE, related_name='transactions')),
        migrations.AddField(model_name='wallettransaction', name='order', field=models.ForeignKey('orders.order', null=True, blank=True, on_delete=models.SET_NULL, related_name='wallet_transactions')),
        migrations.AddField(model_name='loyaltytier', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='loyalty_tiers')),
        migrations.AddField(model_name='loyaltycampaign', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='loyalty_campaigns')),
    ]
