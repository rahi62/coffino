from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('businesses', '0001_initial'),
        ('catalog', '0001_initial'),
        ('inventory', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='inventoryitem', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='inventory_items')),
        migrations.AddField(model_name='stockmovement', name='item', field=models.ForeignKey('inventory.inventoryitem', on_delete=models.PROTECT, related_name='movements')),
        migrations.AddField(model_name='stockmovement', name='lot', field=models.ForeignKey('inventory.inventorylot', null=True, blank=True, on_delete=models.SET_NULL, related_name='movements')),
        migrations.AddField(model_name='recipeitem', name='product', field=models.ForeignKey('catalog.product', on_delete=models.CASCADE, related_name='recipe_items')),
        migrations.AddField(model_name='recipeitem', name='inventory_item', field=models.ForeignKey('inventory.inventoryitem', on_delete=models.PROTECT, related_name='recipe_usages')),
        migrations.AddField(model_name='wasterecord', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='waste_records')),
        migrations.AddField(model_name='wasterecord', name='item', field=models.ForeignKey('inventory.inventoryitem', on_delete=models.PROTECT, related_name='waste_records')),
        migrations.AddField(model_name='wasterecord', name='created_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL)),
        migrations.AddField(model_name='inventorycount', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='inventory_counts')),
        migrations.AddField(model_name='inventorycount', name='counted_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL, related_name='inventory_counts')),
        migrations.AddField(model_name='inventorycount', name='posted_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL, related_name='posted_inventory_counts')),
        migrations.AddField(model_name='inventorycountline', name='count', field=models.ForeignKey('inventory.inventorycount', on_delete=models.CASCADE, related_name='lines')),
        migrations.AddField(model_name='inventorycountline', name='item', field=models.ForeignKey('inventory.inventoryitem', on_delete=models.PROTECT, related_name='count_lines')),
        migrations.AddField(model_name='stocktransfer', name='source_branch', field=models.ForeignKey('businesses.branch', on_delete=models.PROTECT, related_name='outgoing_stock_transfers')),
        migrations.AddField(model_name='stocktransfer', name='destination_branch', field=models.ForeignKey('businesses.branch', on_delete=models.PROTECT, related_name='incoming_stock_transfers')),
        migrations.AddField(model_name='stocktransfer', name='requested_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL, related_name='requested_stock_transfers')),
        migrations.AddField(model_name='stocktransfer', name='posted_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL, related_name='posted_stock_transfers')),
        migrations.AddField(model_name='stocktransferline', name='transfer', field=models.ForeignKey('inventory.stocktransfer', on_delete=models.CASCADE, related_name='lines')),
        migrations.AddField(model_name='stocktransferline', name='source_item', field=models.ForeignKey('inventory.inventoryitem', on_delete=models.PROTECT, related_name='transfer_out_lines')),
        migrations.AddField(model_name='stocktransferline', name='destination_item', field=models.ForeignKey('inventory.inventoryitem', on_delete=models.PROTECT, related_name='transfer_in_lines')),
        migrations.AddField(model_name='inventorylot', name='item', field=models.ForeignKey('inventory.inventoryitem', on_delete=models.PROTECT, related_name='lots')),
        migrations.AddField(model_name='lotinventorycount', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='lot_inventory_counts')),
        migrations.AddField(model_name='lotinventorycount', name='counted_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL, related_name='lot_counts')),
        migrations.AddField(model_name='lotinventorycount', name='posted_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL, related_name='posted_lot_counts')),
        migrations.AddField(model_name='lotinventorycountline', name='count', field=models.ForeignKey('inventory.lotinventorycount', on_delete=models.CASCADE, related_name='lines')),
        migrations.AddField(model_name='lotinventorycountline', name='lot', field=models.ForeignKey('inventory.inventorylot', on_delete=models.PROTECT, related_name='count_lines')),
    ]
