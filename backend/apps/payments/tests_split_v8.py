from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business,Branch
from apps.catalog.models import Product
from apps.orders.models import Order,OrderItem
from apps.payments.services import create_item_splits,settle_bill_split
class ItemSplitTests(TestCase):
    def test_item_quantities_allocate_and_totals_reconcile(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='M');p=Product.objects.create(branch=br,name='Coffee',price=1000)
        o=Order.objects.create(branch=br,order_number=1,order_type='DINE_IN',subtotal=3000,discount_total=300,tax_total=270,service_charge_total=270,grand_total=3240)
        oi=OrderItem.objects.create(order=o,product=p,product_name='Coffee',quantity=3,unit_price=1000,line_total=3000)
        splits=create_item_splits(o,[{'label':'A','lines':[{'order_item':oi.id,'quantity':1}]},{'label':'B','lines':[{'order_item':oi.id,'quantity':2}]}])
        self.assertEqual(sum((x.total for x in splits),Decimal('0')),Decimal('3240'))
        settle_bill_split(splits[0],payments=[{'method':'POS','amount':splits[0].total}])
        splits[0].refresh_from_db();self.assertEqual(splits[0].status,'PAID')
    def test_all_order_quantity_must_be_allocated(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='M');p=Product.objects.create(branch=br,name='Coffee',price=1000)
        o=Order.objects.create(branch=br,order_number=1,order_type='DINE_IN',subtotal=2000,grand_total=2000)
        oi=OrderItem.objects.create(order=o,product=p,product_name='Coffee',quantity=2,unit_price=1000,line_total=2000)
        with self.assertRaises(ValueError):create_item_splits(o,[{'label':'A','lines':[{'order_item':oi.id,'quantity':1}]}])
