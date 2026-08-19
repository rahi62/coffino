from unittest.mock import patch

from django.test import TestCase

from apps.businesses.models import Branch, Business
from apps.online_ordering.models import OnlineMenuSettings, OnlineOrder
from apps.orders.models import Order
from apps.payment_gateway.models import GatewayIntent, PaymentGatewayConfig
from apps.payment_gateway.services import create_payment_intent, verify_payment
from apps.payments.models import Payment


class GatewayTestBase(TestCase):
    def make_online(self, *, deployment='LOCAL', provider='MOCK', callback='http://127.0.0.1:8000', request_url=''):
        business=Business.objects.create(name=f'B-{Business.objects.count()+1}',deployment_type=deployment)
        branch=Branch.objects.create(business=business,name='Main')
        OnlineMenuSettings.objects.create(
            branch=branch,public_slug=f'main-{branch.id}',is_enabled=True,accepting_orders=True,payment_mode='ONLINE'
        )
        config=PaymentGatewayConfig.objects.create(
            branch=branch,provider=provider,is_active=True,callback_base_url=callback,request_url=request_url
        )
        order=Order.objects.create(
            branch=branch,order_number=branch.id,order_type='TAKEAWAY',subtotal=1000,grand_total=1000,status=Order.Status.DRAFT
        )
        payment=Payment.objects.create(
            order=order,amount=1000,method=Payment.Method.ONLINE,status=Payment.Status.PENDING
        )
        online=OnlineOrder.objects.create(
            branch=branch,order=order,payment_mode='ONLINE',status=OnlineOrder.Status.PAYMENT_PENDING
        )
        return business,branch,config,order,payment,online


class MockGatewayTests(GatewayTestBase):
    def test_mock_intent_and_verify(self):
        _,_,_,order,payment,online=self.make_online()
        intent=create_payment_intent(online)
        self.assertEqual(intent.status,GatewayIntent.Status.REDIRECTED)
        intent=verify_payment(online=online,authority=intent.authority,status='OK')
        payment.refresh_from_db();order.refresh_from_db()
        self.assertEqual(intent.status,GatewayIntent.Status.VERIFIED)
        self.assertEqual(payment.status,Payment.Status.SUCCEEDED)
        self.assertEqual(order.payment_status,Order.PaymentStatus.PAID)


class GenericGatewayNetworkSafetyTests(GatewayTestBase):
    @patch('apps.payment_gateway.services.post_json')
    def test_saas_generic_request_uses_public_https_policy(self, post_json):
        post_json.return_value={
            'authority':'AUTH-1',
            'payment_url':'https://8.8.8.8/pay/AUTH-1',
        }
        _,_,_,_,_,online=self.make_online(
            deployment='SAAS',provider='GENERIC',callback='https://1.1.1.1',request_url='https://8.8.4.4/request'
        )
        intent=create_payment_intent(online)
        self.assertEqual(intent.authority,'AUTH-1')
        self.assertEqual(intent.payment_url,'https://8.8.8.8/pay/AUTH-1')
        kwargs=post_json.call_args.kwargs
        self.assertFalse(kwargs['allow_private'])
        self.assertTrue(kwargs['require_https'])

    @patch('apps.payment_gateway.services.post_json')
    def test_saas_rejects_private_payment_redirect_returned_by_provider(self, post_json):
        post_json.return_value={
            'authority':'AUTH-PRIVATE',
            'payment_url':'https://127.0.0.1/pay/AUTH-PRIVATE',
        }
        _,_,_,_,payment,online=self.make_online(
            deployment='SAAS',provider='GENERIC',callback='https://1.1.1.1',request_url='https://8.8.4.4/request'
        )
        with self.assertRaisesRegex(ValueError,'Private/internal'):
            create_payment_intent(online)
        self.assertFalse(GatewayIntent.objects.filter(payment=payment).exists())

    @patch('apps.payment_gateway.services.post_json')
    def test_local_generic_adapter_may_use_private_http(self, post_json):
        post_json.return_value={
            'authority':'LOCAL-1',
            'payment_url':'http://127.0.0.1:19090/pay/LOCAL-1',
        }
        _,_,_,_,_,online=self.make_online(
            deployment='LOCAL',provider='GENERIC',callback='http://127.0.0.1:8000',request_url='http://127.0.0.1:19090/request'
        )
        intent=create_payment_intent(online)
        self.assertEqual(intent.authority,'LOCAL-1')
        kwargs=post_json.call_args.kwargs
        self.assertTrue(kwargs['allow_private'])
        self.assertFalse(kwargs['require_https'])

    def test_saas_rejects_plain_http_callback_before_provider_call(self):
        _,_,_,_,_,online=self.make_online(
            deployment='SAAS',provider='GENERIC',callback='http://127.0.0.1:8000',request_url='https://8.8.4.4/request'
        )
        with self.assertRaisesRegex(ValueError,'HTTPS'):
            create_payment_intent(online)

    @patch('apps.payment_gateway.services.post_json')
    def test_intent_audit_snapshots_drop_custom_secret_and_pan(self, post_json):
        post_json.side_effect=[
            {'authority':'AUTH-AUDIT','payment_url':'https://8.8.8.8/pay/AUTH-AUDIT'},
            {'success':True,'reference_id':'REF-AUDIT','pan':'6037991234567890','provider_secret':'SHOULD-NOT-PERSIST'},
        ]
        _,_,config,_,_,online=self.make_online(
            deployment='SAAS',provider='GENERIC',callback='https://1.1.1.1',request_url='https://8.8.4.4/request'
        )
        config.verify_url='https://8.8.4.4/verify'
        config.extra={'request_payload':{'vendor_secret':'TOP-SECRET','campaign':'summer'}}
        config.save(update_fields=['verify_url','extra','updated_at'])

        intent=create_payment_intent(online)
        request_snapshot=str(intent.request_payload)
        self.assertNotIn('TOP-SECRET',request_snapshot)
        self.assertNotIn('vendor_secret',request_snapshot.replace("'custom_field_names': ['campaign', 'vendor_secret']",''))
        self.assertIn('custom_field_names',intent.request_payload)

        intent=verify_payment(online=online,authority=intent.authority,status='OK')
        verify_snapshot=str(intent.verify_payload)
        self.assertEqual(intent.reference_id,'REF-AUDIT')
        self.assertNotIn('6037991234567890',verify_snapshot)
        self.assertNotIn('SHOULD-NOT-PERSIST',verify_snapshot)
        self.assertNotIn('pan',intent.verify_payload)
        self.assertNotIn('provider_secret',intent.verify_payload)
