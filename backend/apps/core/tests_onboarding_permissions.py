from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.businesses.models import Branch, Business


class OnboardingPermissionBoundaryTests(TestCase):
    def setUp(self):
        self.business=Business.objects.create(name='Scoped Settings Tenant')
        self.branch=Branch.objects.create(business=self.business,name='Main')
        self.settings_operator=User.objects.create_user(
            username='settings-operator',password='password123',business=self.business,
            branch=self.branch,role=User.Role.CASHIER,
            permission_overrides={'settings.manage':True,'business.manage':False},
        )
        self.client=APIClient();self.client.force_authenticate(user=self.settings_operator)

    def test_settings_operator_can_read_readiness_but_cannot_apply_business_preset(self):
        readiness=self.client.get('/api/v1/settings/readiness/')
        self.assertEqual(readiness.status_code,200)

        presets=self.client.get('/api/v1/settings/onboarding/presets/')
        self.assertEqual(presets.status_code,403)

        apply_response=self.client.post('/api/v1/settings/onboarding/apply/',{
            'preset':'CAFE','branch':self.branch.id,'deployment_type':'LOCAL'
        },format='json')
        self.assertEqual(apply_response.status_code,403)
