from django.test import TestCase
from apps.businesses.models import Business,Branch
from apps.catalog.models import Product
from apps.online_ordering.models import OnlineMenuSettings
from apps.online_ordering.services import create_public_order
class OnlineOrderingTests(TestCase):
    def test_pay_at_counter_creates_unpaid_fulfillment_order(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='M');p=Product.objects.create(branch=br,name='Tea',price=1000)
        s=OnlineMenuSettings.objects.create(branch=br,public_slug='m',is_enabled=True,accepting_orders=True,payment_mode='PAY_AT_COUNTER')
        x=create_public_order(settings=s,items=[{'product':p.id,'quantity':1}],customer_name='A',customer_phone='0912',order_type='TAKEAWAY',idempotency_key='x')
        self.assertEqual(x.order.payment_status,'UNPAID');self.assertEqual(x.order.status,'CONFIRMED')
    def test_online_mode_holds_fulfillment_until_payment(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='M');p=Product.objects.create(branch=br,name='Tea',price=1000)
        s=OnlineMenuSettings.objects.create(branch=br,public_slug='m2',is_enabled=True,accepting_orders=True,payment_mode='ONLINE')
        x=create_public_order(settings=s,items=[{'product':p.id,'quantity':1}],order_type='TAKEAWAY',idempotency_key='y')
        self.assertEqual(x.order.status,'DRAFT');self.assertEqual(x.status,'PAYMENT_PENDING');self.assertEqual(x.order.payments.get().status,'PENDING')
