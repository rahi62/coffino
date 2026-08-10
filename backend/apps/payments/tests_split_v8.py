from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business,Branch
from apps.accounts.models import User
from apps.catalog.models import Product
from apps.orders.models import Order,OrderItem
from apps.cashier.models import CashMovement, CashRegister, CashShift
from apps.orders.services import checkout_order
from apps.payments.models import Payment
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

    def test_item_split_api_settles_every_guest_and_reconciles_the_order(self):
        business=Business.objects.create(name='آزمون تقسیم صورت‌حساب')
        branch=Branch.objects.create(business=business,name='شعبه آزمون')
        owner=User.objects.create_user(
            username='split-owner',password='x',business=business,branch=branch,role=User.Role.OWNER,
        )
        product=Product.objects.create(branch=branch,name='آیتم آزمایشی',price=1000)
        order=checkout_order(
            branch=branch,items=[{'product':product,'quantity':3}],order_type='DINE_IN',
            user=owner,defer_payment=True,
        )
        register=CashRegister.objects.create(branch=branch,name='صندوق آزمون تقسیم')
        CashShift.objects.create(register=register,cashier=owner,opening_balance=0,is_open=True)
        item=order.items.get()
        self.client.force_login(owner)

        created=self.client.post(f'/api/v1/orders/{order.id}/bill-splits/',{
            'groups':[
                {'label':'نفر اول','lines':[{'order_item':item.id,'quantity':'1'}]},
                {'label':'نفر دوم','lines':[{'order_item':item.id,'quantity':'2'}]},
            ],
        },content_type='application/json')

        self.assertEqual(created.status_code,201)
        splits=created.json()
        self.assertEqual(len(splits),2)
        self.assertEqual(sum(Decimal(split['total']) for split in splits),Decimal(order.grand_total))

        first=self.client.post(f"/api/v1/bill-splits/{splits[0]['id']}/settle/",{
            'payments':[{'method':'POS','amount':splits[0]['total'],'payer_label':'نفر اول'}],
        },content_type='application/json')
        self.assertEqual(first.status_code,201)
        order.refresh_from_db()
        self.assertEqual(order.payment_status,Order.PaymentStatus.PARTIAL)

        second=self.client.post(f"/api/v1/bill-splits/{splits[1]['id']}/settle/",{
            'payments':[{'method':'CASH','amount':splits[1]['total'],'tendered_amount':splits[1]['total'],'payer_label':'نفر دوم'}],
        },content_type='application/json')
        self.assertEqual(second.status_code,201)
        order.refresh_from_db()
        self.assertEqual(order.payment_status,Order.PaymentStatus.PAID)
        self.assertEqual(Payment.objects.filter(order=order,bill_split__isnull=False,status=Payment.Status.SUCCEEDED).count(),2)
        self.assertEqual(CashMovement.objects.filter(payment__order=order,movement_type=CashMovement.Type.SALE).count(),1)
