from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('businesses', '0001_initial'),
        ('inventory', '0001_initial'),
        ('purchasing', '0001_initial'),
        ('suppliers', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='purchaseinvoice', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='purchase_invoices')),
        migrations.AddField(model_name='purchaseinvoice', name='supplier', field=models.ForeignKey('suppliers.supplier', on_delete=models.PROTECT, related_name='invoices')),
        migrations.AddField(model_name='purchaseinvoice', name='created_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='purchaseitem', name='invoice', field=models.ForeignKey('purchasing.purchaseinvoice', on_delete=models.CASCADE, related_name='items')),
        migrations.AddField(model_name='purchaseitem', name='inventory_item', field=models.ForeignKey('inventory.inventoryitem', on_delete=models.PROTECT, related_name='purchase_items')),
        migrations.AddField(model_name='supplierpayment', name='supplier', field=models.ForeignKey('suppliers.supplier', on_delete=models.PROTECT, related_name='payments')),
        migrations.AddField(model_name='supplierpayment', name='purchase_invoice', field=models.ForeignKey('purchasing.purchaseinvoice', null=True, blank=True, on_delete=models.SET_NULL, related_name='supplier_payments')),
        migrations.AddField(model_name='supplierpayment', name='created_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
    ]
