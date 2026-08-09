from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business, Branch
from apps.inventory.models import InventoryItem, InventoryCount, StockTransfer, StockTransferLine
from apps.inventory.services import create_inventory_count, post_inventory_count, post_stock_transfer

class InventoryCountTests(TestCase):
    def setUp(self):
        b=Business.objects.create(name='B');self.br=Branch.objects.create(business=b,name='Main')
        self.item=InventoryItem.objects.create(branch=self.br,name='Beans',current_stock=10,average_cost=100)

    def test_post_count_creates_variance(self):
        count=create_inventory_count(branch=self.br,title='Count',lines=[{'item':self.item,'counted_quantity':8}])
        post_inventory_count(count)
        self.item.refresh_from_db();count.refresh_from_db()
        self.assertEqual(self.item.current_stock,Decimal('8'))
        self.assertEqual(count.status,InventoryCount.Status.POSTED)
        self.assertEqual(count.lines.get().variance,Decimal('-2'))

    def test_post_rejects_if_stock_changed_after_snapshot(self):
        count=create_inventory_count(branch=self.br,title='Count',lines=[{'item':self.item,'counted_quantity':8}])
        self.item.current_stock=9;self.item.save(update_fields=['current_stock'])
        with self.assertRaises(ValueError): post_inventory_count(count)

class StockTransferTests(TestCase):
    def test_atomic_transfer_moves_quantity_and_cost(self):
        b=Business.objects.create(name='B');a=Branch.objects.create(business=b,name='A');d=Branch.objects.create(business=b,name='D')
        src=InventoryItem.objects.create(branch=a,name='Milk',current_stock=10,average_cost=50)
        dst=InventoryItem.objects.create(branch=d,name='Milk',current_stock=10,average_cost=100)
        t=StockTransfer.objects.create(source_branch=a,destination_branch=d)
        StockTransferLine.objects.create(transfer=t,source_item=src,destination_item=dst,quantity=4)
        post_stock_transfer(t);src.refresh_from_db();dst.refresh_from_db()
        self.assertEqual(src.current_stock,Decimal('6'))
        self.assertEqual(dst.current_stock,Decimal('14'))
        self.assertAlmostEqual(float(dst.average_cost),85.7142857,places=2)
