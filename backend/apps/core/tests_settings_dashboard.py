from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.businesses.models import Business,Branch,BusinessModule
from apps.cashier.models import CashRegister
from apps.catalog.models import Product
from apps.dining.models import Hall,Table
from apps.kitchen.models import PreparationStation
from apps.notifications.models import SmsProviderConfig
from apps.online_ordering.models import OnlineMenuSettings
from apps.payment_gateway.models import PaymentGatewayConfig
from apps.printing.models import PrinterDevice


class SettingsDashboardTests(TestCase):
    def setUp(self):
        self.business=Business.objects.create(name='Settings Tenant')
        self.branch=Branch.objects.create(business=self.business,name='Main')
        self.owner=User.objects.create_user(
            username='settings-owner',password='password123',business=self.business,
            branch=self.branch,role=User.Role.OWNER
        )
        self.waiter=User.objects.create_user(
            username='settings-waiter',password='password123',business=self.business,
            branch=self.branch,role=User.Role.WAITER
        )
        self.hall=Hall.objects.create(branch=self.branch,name='Hall')
        self.table=Table.objects.create(hall=self.hall,number='1',capacity=4)

    def api_client(self,user):
        client=APIClient()
        client.force_authenticate(user=user)
        return client

    def test_owner_can_load_settings_context(self):
        response=self.api_client(self.owner).get('/api/v1/settings/context/')
        self.assertEqual(response.status_code,200)
        body=response.json()
        self.assertEqual(body['business']['id'],self.business.id)
        self.assertEqual(body['branches'][0]['id'],self.branch.id)
        self.assertTrue(body['permissions']['settings.manage'])

    def test_operational_user_cannot_open_settings_context(self):
        response=self.api_client(self.waiter).get('/api/v1/settings/context/')
        self.assertEqual(response.status_code,403)

    def test_operational_user_cannot_open_settings_readiness(self):
        response=self.api_client(self.waiter).get('/api/v1/settings/readiness/')
        self.assertEqual(response.status_code,403)

    def test_operational_user_cannot_use_onboarding_or_health(self):
        client=self.api_client(self.waiter)
        self.assertEqual(client.get('/api/v1/settings/onboarding/presets/').status_code,403)
        self.assertEqual(client.post('/api/v1/settings/onboarding/apply/',{'preset':'CAFE'},format='json').status_code,403)
        self.assertEqual(client.get(f'/api/v1/settings/health/?branch={self.branch.id}').status_code,403)

    def test_readiness_tracks_missing_and_completed_pos_setup(self):
        BusinessModule.objects.create(business=self.business,key='POS',enabled=True)
        client=self.api_client(self.owner)

        first=client.get('/api/v1/settings/readiness/')
        self.assertEqual(first.status_code,200)
        branch=first.json()['branches'][0]
        checks={row['key']:row for row in branch['checks']}
        self.assertEqual(checks['pos_register']['status'],'missing')
        self.assertEqual(checks['catalog_products']['status'],'missing')
        first_score=first.json()['overall']['score']

        CashRegister.objects.create(branch=self.branch,name='Main register',is_active=True)
        Product.objects.create(branch=self.branch,name='Espresso',price=100000,is_available=True)

        second=client.get('/api/v1/settings/readiness/')
        self.assertEqual(second.status_code,200)
        branch=second.json()['branches'][0]
        checks={row['key']:row for row in branch['checks']}
        self.assertEqual(checks['pos_register']['status'],'done')
        self.assertEqual(checks['catalog_products']['status'],'done')
        self.assertGreater(second.json()['overall']['score'],first_score)

    def test_onboarding_preset_bootstraps_safe_operational_defaults(self):
        BusinessModule.objects.create(business=self.business,key='LOYALTY',enabled=True)
        response=self.api_client(self.owner).post('/api/v1/settings/onboarding/apply/',{
            'preset':'CAFE','branch':self.branch.id,'deployment_type':'LOCAL','replace_modules':True,
            'branch_name':'کافه مرکزی','branch_phone':'02100000000','branch_address':'تهران',
            'create_register':True,'register_name':'صندوق ورودی',
            'hall_name':'سالن Wizard','table_count':3,'table_capacity':4,'create_stations':True,
        },format='json')
        self.assertEqual(response.status_code,200)
        self.business.refresh_from_db();self.branch.refresh_from_db()
        self.assertEqual(self.business.business_type,'CAFE')
        self.assertEqual(self.branch.name,'کافه مرکزی')
        self.assertTrue(BusinessModule.objects.get(business=self.business,key='POS').enabled)
        self.assertTrue(BusinessModule.objects.get(business=self.business,key='DINE_IN').enabled)
        self.assertFalse(BusinessModule.objects.get(business=self.business,key='LOYALTY').enabled)
        self.assertTrue(CashRegister.objects.filter(branch=self.branch,name='صندوق ورودی',is_active=True).exists())
        wizard_hall=Hall.objects.get(branch=self.branch,name='سالن Wizard')
        self.assertEqual(Table.objects.filter(hall=wizard_hall).count(),3)
        self.assertGreaterEqual(PreparationStation.objects.filter(branch=self.branch,is_active=True).count(),2)
        self.assertTrue(AuditLog.objects.filter(action='ONBOARDING_PRESET_APPLIED',business=self.business).exists())
        self.assertEqual(response.json()['created']['tables'],3)

    def test_onboarding_catalog_lists_multiple_business_profiles(self):
        response=self.api_client(self.owner).get('/api/v1/settings/onboarding/presets/')
        self.assertEqual(response.status_code,200)
        keys={row['key'] for row in response.json()['presets']}
        self.assertTrue({'CAFE','RESTAURANT','FAST_FOOD','BAKERY','PASTRY','CATERING'}.issubset(keys))

    def test_settings_health_distinguishes_config_network_and_hardware(self):
        for key in ['ONLINE_ORDERING','SMS','PAYMENT_GATEWAY','PRINTING']:
            BusinessModule.objects.create(business=self.business,key=key,enabled=True)
        Product.objects.create(branch=self.branch,name='Espresso',price=100000,is_available=True)
        OnlineMenuSettings.objects.create(
            branch=self.branch,public_slug='settings-main',is_enabled=True,accepting_orders=True,
            payment_mode=OnlineMenuSettings.PaymentMode.ONLINE
        )
        PaymentGatewayConfig.objects.create(
            branch=self.branch,provider=PaymentGatewayConfig.Provider.MOCK,is_active=True,
            callback_base_url='http://127.0.0.1:8000'
        )
        SmsProviderConfig.objects.create(branch=self.branch,provider_name='TEST',endpoint_url='https://sms.example.com/api',is_active=True)
        PrinterDevice.objects.create(branch=self.branch,name='رسید',system_name='Office Printer',is_active=True)

        response=self.api_client(self.owner).get(f'/api/v1/settings/health/?branch={self.branch.id}')
        self.assertEqual(response.status_code,200)
        rows={row['key']:row for row in response.json()['checks']}
        self.assertEqual(rows['online_menu']['status'],'ok')
        self.assertEqual(rows['payment_gateway']['status'],'ok')
        self.assertEqual(rows['sms']['status'],'warning')
        self.assertEqual(rows['printer']['status'],'warning')

        printer=self.api_client(self.owner).post('/api/v1/settings/health/printer/',{
            'branch':self.branch.id,'devices':['Microsoft Print to PDF','Office Printer']
        },format='json')
        self.assertEqual(printer.status_code,200)
        self.assertEqual(printer.json()['check']['status'],'ok')
        self.assertEqual(printer.json()['check']['details']['matched'],1)

    @patch('apps.core.settings_health._safe_http_probe',return_value=(True,405,'Endpoint reachable'))
    def test_live_health_probes_sms_without_sending_message(self,probe):
        BusinessModule.objects.create(business=self.business,key='SMS',enabled=True)
        SmsProviderConfig.objects.create(branch=self.branch,provider_name='TEST',endpoint_url='https://sms.example.com/api',is_active=True)
        response=self.api_client(self.owner).get(f'/api/v1/settings/health/?branch={self.branch.id}&live=1')
        self.assertEqual(response.status_code,200)
        rows={row['key']:row for row in response.json()['checks']}
        self.assertEqual(rows['sms']['status'],'ok')
        self.assertEqual(rows['sms']['details']['http_status'],405)
        probe.assert_called_once()

    def test_waiter_can_operate_table_but_cannot_reconfigure_it(self):
        client=self.api_client(self.waiter)
        patch_response=client.patch(f'/api/v1/tables/{self.table.id}/',{'capacity':8},format='json')
        self.assertEqual(patch_response.status_code,403)
        open_response=client.post(f'/api/v1/tables/{self.table.id}/open_session/',{'customer_count':2},format='json')
        self.assertEqual(open_response.status_code,201)

    def test_disabled_module_gates_operational_permission_but_not_settings(self):
        BusinessModule.objects.create(business=self.business,key='DINE_IN',enabled=False)
        waiter=User.objects.get(pk=self.waiter.pk)
        client=self.api_client(waiter)
        table_response=client.get('/api/v1/tables/')
        self.assertEqual(table_response.status_code,200)
        self.assertEqual(table_response.json(),[])
        owner=User.objects.get(pk=self.owner.pk)
        context=self.api_client(owner).get('/api/v1/settings/context/')
        self.assertEqual(context.status_code,200)
        self.assertTrue(context.json()['permissions']['settings.manage'])
        self.assertFalse(context.json()['permissions']['tables.use'])

    def test_settings_change_creates_business_scoped_audit(self):
        client=self.api_client(self.owner)
        response=client.patch(
            f'/api/v1/branches/{self.branch.id}/',{'phone':'02100000000'},format='json'
        )
        self.assertEqual(response.status_code,200)
        log=AuditLog.objects.filter(action='CONFIG_UPDATED',entity_type='Branch').latest('created_at')
        self.assertEqual(log.business_id,self.business.id)
        self.assertEqual(log.branch_id,self.branch.id)
        self.assertEqual(log.after['phone'],'02100000000')

    def test_business_module_change_is_audited_even_without_branch(self):
        client=self.api_client(self.owner)
        response=client.post('/api/v1/business-modules/',{
            'business':self.business.id,'key':'LOYALTY','enabled':True,'config':{}
        },format='json')
        self.assertEqual(response.status_code,201)
        log=AuditLog.objects.filter(action='CONFIG_CREATED',entity_type='BusinessModule').latest('created_at')
        self.assertEqual(log.business_id,self.business.id)

    def test_owner_can_create_operational_user_from_dashboard(self):
        response=self.api_client(self.owner).post('/api/v1/settings/users/create/',{
            'username':'new-cashier','password':'password123','first_name':'صندوق',
            'role':'CASHIER','branch':self.branch.id,'business':self.business.id
        },format='json')
        self.assertEqual(response.status_code,201)
        user=User.objects.get(username='new-cashier')
        self.assertEqual(user.business_id,self.business.id)
        self.assertEqual(user.branch_id,self.branch.id)
        self.assertTrue(user.check_password('password123'))
        self.assertTrue(AuditLog.objects.filter(action='TEAM_USER_CREATED',entity_id=str(user.id)).exists())

    def test_operational_user_cannot_create_user(self):
        response=self.api_client(self.waiter).post('/api/v1/settings/users/create/',{
            'username':'bad-user','password':'password123','role':'CASHIER','branch':self.branch.id
        },format='json')
        self.assertEqual(response.status_code,403)
        self.assertFalse(User.objects.filter(username='bad-user').exists())

    def test_cash_register_definition_requires_settings_permission(self):
        response=self.api_client(self.waiter).post('/api/v1/cash-registers/',{
            'branch':self.branch.id,'name':'Forbidden register','is_active':True
        },format='json')
        self.assertEqual(response.status_code,403)
        self.assertFalse(CashRegister.objects.filter(name='Forbidden register').exists())
