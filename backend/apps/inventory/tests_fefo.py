from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from apps.businesses.models import Business,Branch
from apps.inventory.models import InventoryItem,InventoryLot,StockMovement
from apps.inventory.lot_services import receive_stock,consume_stock
class FefoTests(TestCase):
    def setUp(self):
        b=Business.objects.create(name='B');self.br=Branch.objects.create(business=b,name='M');self.item=InventoryItem.objects.create(branch=self.br,name='Milk',lot_tracked=True)
    def test_earliest_expiry_is_consumed_first(self):
        receive_stock(item=self.item,quantity=5,unit_cost=10,movement_type=StockMovement.Type.PURCHASE,lot_number='LATE',expires_at=timezone.now()+timedelta(days=10))
        receive_stock(item=self.item,quantity=3,unit_cost=20,movement_type=StockMovement.Type.PURCHASE,lot_number='EARLY',expires_at=timezone.now()+timedelta(days=2))
        consume_stock(item=self.item,quantity=4,movement_type=StockMovement.Type.SALE,reference_type='T',reference_id='1')
        early=InventoryLot.objects.get(item=self.item,lot_number='EARLY');late=InventoryLot.objects.get(item=self.item,lot_number='LATE')
        self.assertEqual(early.quantity_remaining,Decimal('0'));self.assertEqual(late.quantity_remaining,Decimal('4'))
    def test_expired_lot_is_not_automatic_stock(self):
        receive_stock(item=self.item,quantity=2,unit_cost=10,movement_type=StockMovement.Type.PURCHASE,lot_number='OLD',expires_at=timezone.now()-timedelta(days=1))
        with self.assertRaises(ValueError):consume_stock(item=self.item,quantity=1,movement_type=StockMovement.Type.SALE)
