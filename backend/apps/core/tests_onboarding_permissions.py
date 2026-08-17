from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.businesses.models import Branch, Business, BusinessModule


class OnboardingPermissionBoundaryTests(TestCase):
    def setUp(self):
        self.business=Business.objects.create(name='Scoped Settings Tenant')
        self.branch=Branch.objects.create(business=self.business,name='Main')
        self.owner=User.objects.create_user(
            username='scoped-owner',password='password123',business=self.business,
            branch=self.branch,role=User.Role.OWNER,
        )
        self.settings_operator=User.objects.create_user(
            username='settings-operator',password='password123',business=self.business,
            branch=self.branch,role=User.Role.CASHIER,
            permission_overrides={'settings.manage':True,'business.manage':False},
        )

    def api_client(self,user):
        client=APIClient();client.force_authenticate(user=user);return client

    def test_settings_operator_can_read_readiness_but_cannot_apply_business_preset(self):
        client=self.api_client(self.settings_operator)
        readiness=client.get('/api/v1/settings/readiness/')
        self.assertEqual(readiness.status_code,200)

        presets=client.get('/api/v1/settings/onboarding/presets/')
        self.assertEqual(presets.status_code,403)

        apply_response=client.post('/api/v1/settings/onboarding/apply/',{
            'preset':'CAFE','branch':self.branch.id,'deployment_type':'LOCAL'
        },format='json')
        self.assertEqual(apply_response.status_code,403)

    def test_replace_preset_creates_explicit_disabled_rows_for_non_preset_modules(self):
        response=self.api_client(self.owner).post('/api/v1/settings/onboarding/apply/',{
            'preset':'CAFE','branch':self.branch.id,'deployment_type':'LOCAL','replace_modules':True
        },format='json')
        self.assertEqual(response.status_code,200)
        self.assertTrue(BusinessModule.objects.get(business=self.business,key='POS').enabled)
        self.assertTrue(BusinessModule.objects.get(business=self.business,key='CORE').enabled)
        self.assertFalse(BusinessModule.objects.get(business=self.business,key='GIFT_CARD').enabled)
        self.assertFalse(BusinessModule.objects.get(business=self.business,key='PAYMENT_GATEWAY').enabled)
