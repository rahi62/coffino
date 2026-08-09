from django.contrib import admin
from .models import ProductionFormula, ProductionFormulaItem, ProductionBatch, ProductionBatchIngredient
admin.site.register(ProductionFormula);admin.site.register(ProductionFormulaItem);admin.site.register(ProductionBatch);admin.site.register(ProductionBatchIngredient)
