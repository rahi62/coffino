from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('businesses', '0001_initial'),
        ('catalog', '0001_initial'),
        ('customers', '0001_initial'),
        ('dining', '0001_initial'),
        ('discounts', '0001_initial'),
        ('orders', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='order', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='orders')),
        migrations.AddField(model_name='order', name='customer', field=models.ForeignKey('customers.customer', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='order', name='table_session', field=models.ForeignKey('dining.tablesession', null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')),
        migrations.AddField(model_name='order', name='discount_rule', field=models.ForeignKey('discounts.discountrule', null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')),
        migrations.AddField(model_name='order', name='created_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='orderitem', name='order', field=models.ForeignKey('orders.order', on_delete=models.CASCADE, related_name='items')),
        migrations.AddField(model_name='orderitem', name='product', field=models.ForeignKey('catalog.product', on_delete=models.PROTECT)),
        migrations.AddField(model_name='approvalrequest', name='order', field=models.ForeignKey('orders.order', on_delete=models.CASCADE, related_name='approval_requests')),
        migrations.AddField(model_name='approvalrequest', name='requested_by', field=models.ForeignKey('accounts.user', on_delete=models.PROTECT, related_name='requested_approvals')),
        migrations.AddField(model_name='approvalrequest', name='approved_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.PROTECT, related_name='decided_approvals')),
    ]
