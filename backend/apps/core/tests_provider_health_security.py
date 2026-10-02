from django.test import TestCase

from apps.businesses.models import Branch, Business, BusinessModule
from apps.catalog.models import Product
from apps.core.settings_health import settings_health_payload
from apps.notifications.models import SmsProviderConfig
from apps.online_ordering.models import OnlineMenuSettings
from apps.payment_gateway.models import PaymentGatewayConfig


class ProviderHealthSecurityTests(TestCase):
    def setUp(self):
        self.business=Business.objects.create(name='Cloud Tenant',deployment_type='SAAS')
        self.branch=Branch.objects.create(business=self.business,name='Main')

    def row(self,key):
        payload=settings_health_payload(self.branch,live=False)
        return next(row for row in payload['checks'] if row['key']==key)

    def test_saas_sms_plain_http_private_target_is_blocker(self):
        BusinessModule.objects.create(business=self.business,key='SMS',enabled=True)
        SmsProviderConfig.objects.create(
            branch=self.branch,provider_name='GENERIC',endpoint_url='http://127.0.0.1:9000/send',is_active=True
        )
        row=self.row('sms')
        self.assertEqual(row['status'],'error')
        self.assertIn('HTTPS',row['message'])

    def test_saas_online_menu_requires_public_https_base(self):
        BusinessModule.objects.create(business=self.business,key='ONLINE_ORDERING',enabled=True)
        Product.objects.create(branch=self.branch,name='Coffee',price=1000,is_available=True)
        OnlineMenuSettings.objects.create(
            branch=self.branch,public_slug='cloud-main',public_base_url='http://127.0.0.1:3000',
            is_enabled=True,accepting_orders=True
        )
        row=self.row('online_menu')
        self.assertEqual(row['status'],'error')
        self.assertIn('HTTPS',row['message'])

    def test_saas_mock_gateway_requires_https_callback(self):
        BusinessModule.objects.create(business=self.business,key='PAYMENT_GATEWAY',enabled=True)
        PaymentGatewayConfig.objects.create(
            branch=self.branch,provider=PaymentGatewayConfig.Provider.MOCK,is_active=True,
            callback_base_url='http://127.0.0.1:8000'
        )
        row=self.row('payment_gateway')
        self.assertEqual(row['status'],'error')
        self.assertIn('HTTPS',row['message'])

    def test_local_provider_may_use_private_http_for_local_bridge(self):
        self.business.deployment_type='LOCAL';self.business.save(update_fields=['deployment_type','updated_at'])
        BusinessModule.objects.create(business=self.business,key='SMS',enabled=True)
        SmsProviderConfig.objects.create(
            branch=self.branch,provider_name='LOCAL_BRIDGE',endpoint_url='http://127.0.0.1:9000/send',is_active=True
        )
        row=self.row('sms')
        self.assertEqual(row['status'],'warning')
