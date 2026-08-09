from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.businesses.models import Business,Branch
from apps.catalog.models import Product
from apps.online_ordering.models import OnlineMenuSettings
from apps.orders.models import Order


class PublicApiSafetyTests(TestCase):
    def setUp(self):
        business=Business.objects.create(name='Public Test')
        self.branch=Branch.objects.create(business=business,name='Main')
        self.product=Product.objects.create(
            branch=self.branch,name='Coffee',price=1000,is_available=True
        )
        self.settings=OnlineMenuSettings.objects.create(
            branch=self.branch,public_slug='public-test',is_enabled=True,
            accepting_orders=True,payment_mode=OnlineMenuSettings.PaymentMode.ONLINE,
            allow_takeaway=True
        )
        self.client=APIClient()

    @patch('apps.core.api.public.create_payment_intent')
    def test_unexpected_payment_error_is_generic_and_rolls_back_order(self,mock_intent):
        mock_intent.side_effect=RuntimeError('SECRET_PROVIDER_STACK_TRACE')
        response=self.client.post('/api/v1/public/menu/public-test/orders/',{
            'items':[{'product':self.product.id,'quantity':1}],
            'order_type':'TAKEAWAY',
            'customer_name':'A',
            'customer_phone':'09120000000',
        },format='json')

        self.assertEqual(response.status_code,503)
        body=response.json()
        self.assertEqual(body['error']['code'],'payment_initialization_failed')
        self.assertNotIn('SECRET_PROVIDER_STACK_TRACE',str(body))
        self.assertEqual(Order.objects.count(),0)

    def test_invalid_product_returns_stable_public_error(self):
        response=self.client.post('/api/v1/public/menu/public-test/orders/',{
            'items':[{'product':999999,'quantity':1}],
            'order_type':'TAKEAWAY',
        },format='json')
        self.assertEqual(response.status_code,400)
        self.assertEqual(response.json()['error']['code'],'invalid_product')
