from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.businesses.models import Business,Branch,BusinessModule
from apps.cashier.models import CashRegister
from apps.dining.models import Hall,Table


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

    def test_waiter_can_operate_table_but_cannot_reconfigure_it(self):
        client=self.api_client(self.waiter)
        patch=client.patch(f'/api/v1/tables/{self.table.id}/',{'capacity':8},format='json')
        self.assertEqual(patch.status_code,403)
        open_response=client.post(f'/api/v1/tables/{self.table.id}/open_session/',{'customer_count':2},format='json')
        self.assertEqual(open_response.status_code,201)

    def test_disabled_module_gates_operational_permission_but_not_settings(self):
        BusinessModule.objects.create(business=self.business,key='DINE_IN',enabled=False)
        # Force fresh authenticated user objects so the permission cache is empty.
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
