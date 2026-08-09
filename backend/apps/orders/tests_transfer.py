from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business,Branch
from apps.catalog.models import Product
from apps.orders.models import Order,OrderItem
from apps.orders.services import transfer_order_items

class OrderTransferTests(TestCase):
    def test_partial_item_transfer_recalculates_both_orders(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='Main')
        p=Product.objects.create(branch=br,name='Latte',price=100)
        a=Order.objects.create(branch=br,order_number=1,order_type='DINE_IN',subtotal=200,grand_total=200)
        d=Order.objects.create(branch=br,order_number=2,order_type='DINE_IN',subtotal=0,grand_total=0)
        item=OrderItem.objects.create(order=a,product=p,product_name='Latte',quantity=2,unit_price=100,line_total=200)
        transfer_order_items(source_order=a,destination_order=d,lines=[{'order_item':item.id,'quantity':1}])
        a.refresh_from_db();d.refresh_from_db()
        self.assertEqual(a.subtotal,Decimal('100'))
        self.assertEqual(d.subtotal,Decimal('100'))
        self.assertEqual(a.items.get().quantity,Decimal('1'))
        self.assertEqual(d.items.get().quantity,Decimal('1'))
