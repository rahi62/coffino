from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business, Branch
from apps.inventory.models import InventoryItem
from apps.production.models import ProductionFormula, ProductionFormulaItem, ProductionBatch
from apps.production.services import post_production_batch

class ProductionBatchTests(TestCase):
    def test_batch_consumes_inputs_and_creates_finished_goods_cost(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='Main')
        flour=InventoryItem.objects.create(branch=br,name='Flour',current_stock=1000,average_cost=2)
        out=InventoryItem.objects.create(branch=br,name='Cake',current_stock=0,average_cost=0)
        formula=ProductionFormula.objects.create(branch=br,name='10 cakes',output_item=out,output_quantity=10)
        ProductionFormulaItem.objects.create(formula=formula,inventory_item=flour,quantity=500)
        batch=ProductionBatch.objects.create(branch=br,formula=formula,multiplier=1)
        post_production_batch(batch);flour.refresh_from_db();out.refresh_from_db();batch.refresh_from_db()
        self.assertEqual(flour.current_stock,Decimal('500'))
        self.assertEqual(out.current_stock,Decimal('10'))
        self.assertEqual(batch.total_cost,Decimal('1000'))
        self.assertEqual(batch.unit_cost,Decimal('100'))
