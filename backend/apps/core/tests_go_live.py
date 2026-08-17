from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.businesses.models import Branch, Business, BusinessModule
from apps.core.onboarding import ALL_MODULE_KEYS


class GoLiveGuardTests(TestCase):
    def setUp(self):
        self.business=Business.objects.create(name='Go Live Tenant',business_type='CAFE',deployment_type='LOCAL')
        self.branch=Branch.objects.create(business=self.business,name='Main',address='Tehran',phone='02100000000')
        self.owner=User.objects.create(username='go-live-owner',business=self.business,branch=self.branch,role=User.Role.OWNER,is_active=True)
        self.waiter=User.objects.create(username='go-live-waiter',business=self.business,branch=self.branch,role=User.Role.WAITER,is_active=True)

    def client_for(self,user):
        client=APIClient();client.force_authenticate(user=user);return client

    def write_explicit_module_state(self):
        for key in ALL_MODULE_KEYS:
            BusinessModule.objects.create(business=self.business,key=key,enabled=(key=='CORE'))

    def test_profiles_are_available_to_settings_manager(self):
        response=self.client_for(self.owner).get('/api/v1/settings/deployment-profiles/')
        self.assertEqual(response.status_code,200)
        profiles={row['key']:row for row in response.json()['profiles']}
        self.assertEqual(set(profiles),{'LOCAL','SAAS','DEDICATED'})
        self.assertEqual(profiles['LOCAL']['database'],'SQLite محلی')
        self.assertIn('DATABASE_URL',profiles['SAAS']['environment_template'])

    @override_settings(DEBUG=False,SECRET_KEY='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',ENVIRONMENT='local',ALLOWED_HOSTS=['127.0.0.1','localhost'],SECURE_SSL_REDIRECT=False)
    def test_local_business_can_be_delivery_ready_when_state_is_explicit(self):
        self.write_explicit_module_state()
        response=self.client_for(self.owner).get('/api/v1/settings/go-live/')
        self.assertEqual(response.status_code,200)
        body=response.json()
        self.assertTrue(body['summary']['ready'])
        self.assertEqual(body['summary']['blockers'],0)
        checks={row['key']:row for row in body['business_checks']}
        self.assertEqual(checks['module_state']['status'],'ok')
        self.assertEqual(body['next_action'],'ready_for_delivery')

    @override_settings(DEBUG=False,SECRET_KEY='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',ENVIRONMENT='local',ALLOWED_HOSTS=['127.0.0.1','localhost'],SECURE_SSL_REDIRECT=False)
    def test_implicit_module_state_blocks_go_live(self):
        BusinessModule.objects.create(business=self.business,key='CORE',enabled=True)
        response=self.client_for(self.owner).get('/api/v1/settings/go-live/')
        self.assertEqual(response.status_code,200)
        body=response.json()
        self.assertFalse(body['summary']['ready'])
        module_check={row['key']:row for row in body['business_checks']}['module_state']
        self.assertEqual(module_check['status'],'error')
        self.assertIn('POS',module_check['detail'])

    def test_operational_user_cannot_view_delivery_guard(self):
        client=self.client_for(self.waiter)
        self.assertEqual(client.get('/api/v1/settings/go-live/').status_code,403)
        self.assertEqual(client.get('/api/v1/settings/deployment-profiles/').status_code,403)
