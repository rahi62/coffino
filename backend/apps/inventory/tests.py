from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business, Branch
from apps.inventory.models import InventoryItem
from apps.inventory.services import record_waste
class WasteTests(TestCase):
    def test_waste_decrements_stock_and_snapshots_cost(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='M')
        item=InventoryItem.objects.create(branch=br,name='Milk',current_stock=10,average_cost=50)
        rec=record_waste(item=item,quantity=2,reason='spill')
        item.refresh_from_db()
        self.assertEqual(item.current_stock,Decimal('8'))
        self.assertEqual(rec.total_cost,Decimal('100'))
