from django.test import TestCase
from apps.businesses.models import Business, Branch
from apps.catalog.models import Product
from apps.orders.services import checkout_order

class CheckoutIdempotencyTests(TestCase):
    def setUp(self):
        b=Business.objects.create(name='B')
        self.branch=Branch.objects.create(business=b,name='Main')
        self.product=Product.objects.create(branch=self.branch,name='Water',price=1000,is_available=True)

    def test_same_key_same_payload_returns_same_order(self):
        payload=[{'product':self.product,'quantity':1}]
        a=checkout_order(
            branch=self.branch,items=payload,order_type='TAKEAWAY',
            payment_method='POS',idempotency_key='same-key'
        )
        b=checkout_order(
            branch=self.branch,items=payload,order_type='TAKEAWAY',
            payment_method='POS',idempotency_key='same-key'
        )
        self.assertEqual(a.id,b.id)

    def test_same_key_different_payload_is_rejected(self):
        checkout_order(
            branch=self.branch,items=[{'product':self.product,'quantity':1}],
            order_type='TAKEAWAY',payment_method='POS',idempotency_key='same-key'
        )
        with self.assertRaises(ValueError):
            checkout_order(
                branch=self.branch,items=[{'product':self.product,'quantity':2}],
                order_type='TAKEAWAY',payment_method='POS',idempotency_key='same-key'
            )
