from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('businesses', '0001_initial'),
        ('inventory', '0001_initial'),
        ('production', '0001_initial'),
    ]
    operations = [
        migrations.AddField(model_name='productionformula', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='production_formulas')),
        migrations.AddField(model_name='productionformula', name='output_item', field=models.ForeignKey('inventory.inventoryitem', on_delete=models.PROTECT, related_name='production_formulas')),
        migrations.AddField(model_name='productionformulaitem', name='formula', field=models.ForeignKey('production.productionformula', on_delete=models.CASCADE, related_name='ingredients')),
        migrations.AddField(model_name='productionformulaitem', name='inventory_item', field=models.ForeignKey('inventory.inventoryitem', on_delete=models.PROTECT, related_name='production_formula_usages')),
        migrations.AddField(model_name='productionbatch', name='branch', field=models.ForeignKey('businesses.branch', on_delete=models.CASCADE, related_name='production_batches')),
        migrations.AddField(model_name='productionbatch', name='formula', field=models.ForeignKey('production.productionformula', on_delete=models.PROTECT, related_name='batches')),
        migrations.AddField(model_name='productionbatch', name='created_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_production_batches')),
        migrations.AddField(model_name='productionbatch', name='posted_by', field=models.ForeignKey('accounts.user', null=True, blank=True, on_delete=models.SET_NULL, related_name='posted_production_batches')),
        migrations.AddField(model_name='productionbatchingredient', name='batch', field=models.ForeignKey('production.productionbatch', on_delete=models.CASCADE, related_name='ingredient_snapshots')),
        migrations.AddField(model_name='productionbatchingredient', name='inventory_item', field=models.ForeignKey('inventory.inventoryitem', on_delete=models.PROTECT)),
    ]
