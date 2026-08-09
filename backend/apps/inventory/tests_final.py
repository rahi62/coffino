from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business,Branch
from apps.inventory.models import InventoryItem,InventoryLot,LotInventoryCount
from apps.inventory.services import create_lot_count,post_lot_count

class LotCountFinalTests(TestCase):
    def test_lot_count_updates_lot_and_item_total(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='Main')
        item=InventoryItem.objects.create(branch=br,name='Milk',current_stock=10,average_cost=50)
        lot=InventoryLot.objects.create(item=item,lot_number='L1',quantity_received=10,quantity_remaining=10,unit_cost=50)
        count=create_lot_count(branch=br,title='Count',lines=[{'lot':lot,'counted_quantity':8}])
        post_lot_count(count);lot.refresh_from_db();item.refresh_from_db();count.refresh_from_db()
        self.assertEqual(lot.quantity_remaining,Decimal('8'))
        self.assertEqual(item.current_stock,Decimal('8'))
        self.assertEqual(count.status,LotInventoryCount.Status.POSTED)
