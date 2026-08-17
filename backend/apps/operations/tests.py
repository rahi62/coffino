import base64
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.businesses.models import Business
from .models import DeviceEvent, DeviceInstallation, DiagnosticRequest, ReleasePolicy
from .services import canonicalize


class OperationsControlPlaneTests(APITestCase):
    def setUp(self):
        self.private=Ed25519PrivateKey.generate()
        self.public_pem=self.private.public_key().public_bytes(
            serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        self.machine_hash='a'*64
        self.installation_id=uuid.uuid4()
        self.business=Business.objects.create(name='Ops Tenant')
        self.owner=User.objects.create_user(username='ops-owner',password='x',business=self.business,role=User.Role.OWNER)
        self.platform=User.objects.create_superuser(username='ops-platform',password='x',email='platform@example.com')

    def license_document(self,**extra):
        payload={
            'product':'cafino-local','license_id':'LIC-OPS-1','machine_hash':self.machine_hash,
            'customer':'Ops Cafe','business_id':self.business.id,
        }
        payload.update(extra)
        signature=self.private.sign(canonicalize(payload).encode('utf-8'))
        return {'payload':payload,'signature':base64.b64encode(signature).decode('ascii')}

    def register(self,telemetry=True):
        with override_settings(CAF_INO_LICENSE_PUBLIC_KEY_PEM=self.public_pem,CAF_INO_LICENSE_PUBLIC_KEY_PATH=''):
            return self.client.post('/api/ops/v1/register/',{
                'license_document':self.license_document(),
                'machine_hash':self.machine_hash,
                'installation_id':str(self.installation_id),
                'current_version':'1.2.0','channel':'stable','platform':'win32','arch':'x64',
                'telemetry_enabled':telemetry,
            },format='json')

    def test_signed_license_registers_device_and_only_stores_token_hash(self):
        response=self.register()
        self.assertEqual(response.status_code,201,response.data)
        token=response.data['device_token']
        device=DeviceInstallation.objects.get()
        self.assertNotEqual(device.token_hash,token)
        self.assertEqual(len(device.token_hash),64)
        self.assertEqual(device.business,self.business)
        self.assertEqual(device.license_id,'LIC-OPS-1')

    def test_invalid_license_signature_is_rejected(self):
        document=self.license_document()
        document['payload']['license_id']='TAMPERED'
        with override_settings(CAF_INO_LICENSE_PUBLIC_KEY_PEM=self.public_pem,CAF_INO_LICENSE_PUBLIC_KEY_PATH=''):
            response=self.client.post('/api/ops/v1/register/',{
                'license_document':document,'machine_hash':self.machine_hash,
                'installation_id':str(self.installation_id),'current_version':'1.2.0',
            },format='json')
        self.assertEqual(response.status_code,400)
        self.assertEqual(DeviceInstallation.objects.count(),0)

    def test_device_token_auth_and_deterministic_rollout(self):
        registered=self.register();token=registered.data['device_token']
        ReleasePolicy.objects.create(channel='stable',target_version='1.3.0',rollout_percent=0)
        headers={'HTTP_AUTHORIZATION':f'Bearer {token}'}
        first=self.client.get('/api/ops/v1/policy/',**headers)
        second=self.client.get('/api/ops/v1/policy/',**headers)
        self.assertEqual(first.status_code,200)
        self.assertFalse(first.data['update_allowed'])
        self.assertEqual(first.data['rollout_bucket'],second.data['rollout_bucket'])
        policy=ReleasePolicy.objects.get(channel='stable')
        policy.blocked_versions=['1.2.0'];policy.save()
        blocked=self.client.get('/api/ops/v1/policy/',**headers)
        self.assertTrue(blocked.data['current_blocked'])
        self.assertTrue(blocked.data['must_update'])
        self.assertTrue(blocked.data['update_allowed'])
        self.assertTrue(blocked.data['core_operations_allowed'])
        self.assertFalse(blocked.data['remote_commands_allowed'])

    def test_heartbeat_returns_pending_diagnostic_request(self):
        registered=self.register();token=registered.data['device_token']
        device=DeviceInstallation.objects.get()
        diagnostic=DiagnosticRequest.objects.create(installation=device)
        response=self.client.post('/api/ops/v1/heartbeat/',{
            'current_version':'1.2.0','channel':'stable','platform':'win32','arch':'x64',
            'app_health':'healthy','telemetry_enabled':True,'last_backup_ok':True,
            'last_update_status':'current',
        },format='json',HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(response.data['diagnostic_request_id'],str(diagnostic.request_id))
        device.refresh_from_db();self.assertEqual(device.app_health,'healthy')

    def test_event_endpoint_rejects_raw_message_fields(self):
        registered=self.register();token=registered.data['device_token']
        response=self.client.post('/api/ops/v1/events/',{
            'event_type':'crash','severity':'error','app_version':'1.2.0',
            'component':'electron','fingerprint':'b'*64,'message':'raw exception text must never be accepted',
        },format='json',HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code,400)
        self.assertEqual(DeviceEvent.objects.count(),0)

    def test_diagnostic_snapshot_is_allowlisted(self):
        registered=self.register();token=registered.data['device_token']
        diagnostic=DiagnosticRequest.objects.create(installation=DeviceInstallation.objects.get())
        bad=self.client.post('/api/ops/v1/diagnostics/',{
            'request_id':str(diagnostic.request_id),
            'snapshot':{'app_version':'1.2.0','customer_name':'secret'},
        },format='json',HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(bad.status_code,400)
        good=self.client.post('/api/ops/v1/diagnostics/',{
            'request_id':str(diagnostic.request_id),
            'snapshot':{
                'app_version':'1.2.0','release_channel':'stable','platform':'win32','arch':'x64',
                'backend_healthy':True,'uptime_seconds':120,'db_size_bytes':1000,'free_disk_bytes':5000,
                'backup_count':2,'latest_backup_age_hours':3.5,'update_status':'current',
                'adapter_printer':'SYSTEM','adapter_pager':'NONE','adapter_pos':'MANUAL',
            },
        },format='json',HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(good.status_code,200,good.data)
        diagnostic.refresh_from_db();self.assertEqual(diagnostic.status,'completed')
        self.assertNotIn('customer_name',diagnostic.snapshot)

    def test_tenant_owner_only_sees_assigned_business_devices(self):
        self.register()
        other_business=Business.objects.create(name='Other')
        DeviceInstallation.objects.create(
            token_hash='f'*64,license_id='OTHER',machine_hash='c'*64,current_version='1.0.0',business=other_business,
        )
        self.client.force_authenticate(self.owner)
        response=self.client.get('/api/v1/operations/devices/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(len(response.data),1)
        self.assertEqual(response.data[0]['license_id'],'LIC-OPS-1')

    def test_release_policy_mutation_requires_platform_admin(self):
        ReleasePolicy.objects.create(channel='stable')
        self.client.force_authenticate(self.owner)
        denied=self.client.patch('/api/v1/operations/policies/stable/',{'rollout_percent':25},format='json')
        self.assertEqual(denied.status_code,403)
        self.client.force_authenticate(self.platform)
        allowed=self.client.patch('/api/v1/operations/policies/stable/',{'rollout_percent':25},format='json')
        self.assertEqual(allowed.status_code,200)
        self.assertEqual(allowed.data['rollout_percent'],25)
