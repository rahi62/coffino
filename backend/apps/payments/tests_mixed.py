from decimal import Decimal
from django.test import TestCase
from apps.businesses.models import Business, Branch
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.payments.services import settle_order

class MixedPaymentTests(TestCase):
    def test_two_tenders_settle_one_order(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='Main')
        order=Order.objects.create(branch=br,order_number=1,order_type='TAKEAWAY',subtotal=1000,grand_total=1000)
        rows=settle_order(order,payments=[
            {'method':'POS','amount':400,'payer_label':'نفر ۱'},
            {'method':'CREDIT','amount':600,'payer_label':'نفر ۲'},
        ])
        order.refresh_from_db()
        self.assertEqual(len(rows),2)
        self.assertEqual(order.payment_status,Order.PaymentStatus.PAID)
        self.assertEqual(Payment.objects.filter(order=order).count(),2)

    def test_tender_sum_must_match_remaining(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='Main')
        order=Order.objects.create(branch=br,order_number=1,order_type='TAKEAWAY',subtotal=1000,grand_total=1000)
        with self.assertRaises(ValueError):
            settle_order(order,payments=[{'method':'POS','amount':900}])
