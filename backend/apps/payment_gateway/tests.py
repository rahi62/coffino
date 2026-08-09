from django.test import TestCase
from apps.businesses.models import Business,Branch
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.online_ordering.models import OnlineMenuSettings,OnlineOrder
from apps.payment_gateway.models import PaymentGatewayConfig,GatewayIntent
from apps.payment_gateway.services import create_payment_intent,verify_payment

class MockGatewayTests(TestCase):
    def test_mock_intent_and_verify(self):
        b=Business.objects.create(name='B');br=Branch.objects.create(business=b,name='Main')
        OnlineMenuSettings.objects.create(branch=br,public_slug='main',is_enabled=True,accepting_orders=True,payment_mode='ONLINE')
        PaymentGatewayConfig.objects.create(branch=br,provider='MOCK',is_active=True,callback_base_url='http://127.0.0.1:8000')
        order=Order.objects.create(branch=br,order_number=1,order_type='TAKEAWAY',subtotal=1000,grand_total=1000,status=Order.Status.DRAFT)
        payment=Payment.objects.create(order=order,amount=1000,method=Payment.Method.ONLINE,status=Payment.Status.PENDING)
        online=OnlineOrder.objects.create(branch=br,order=order,payment_mode='ONLINE',status=OnlineOrder.Status.PAYMENT_PENDING)
        intent=create_payment_intent(online)
        self.assertEqual(intent.status,GatewayIntent.Status.REDIRECTED)
        intent=verify_payment(online=online,authority=intent.authority,status='OK')
        payment.refresh_from_db();order.refresh_from_db()
        self.assertEqual(intent.status,GatewayIntent.Status.VERIFIED)
        self.assertEqual(payment.status,Payment.Status.SUCCEEDED)
        self.assertEqual(order.payment_status,Order.PaymentStatus.PAID)
