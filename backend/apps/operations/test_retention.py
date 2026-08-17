from datetime import timedelta

from django.test import TestCase,override_settings
from django.utils import timezone

from .models import DeviceEvent,DeviceInstallation,DiagnosticRequest
from .tasks import prune_operations_history


class OperationsRetentionTests(TestCase):
    def setUp(self):
        self.device=DeviceInstallation.objects.create(
            token_hash='a'*64,license_id='RETENTION',machine_hash='b'*64,current_version='1.0.0'
        )

    @override_settings(CAF_INO_OPS_EVENT_RETENTION_DAYS=30,CAF_INO_OPS_DIAGNOSTIC_RETENTION_DAYS=10)
    def test_old_events_and_completed_diagnostics_are_pruned(self):
        old_event=DeviceEvent.objects.create(
            installation=self.device,event_type=DeviceEvent.Type.CRASH,severity=DeviceEvent.Severity.ERROR,
            fingerprint='c'*64,occurred_at=timezone.now()-timedelta(days=31)
        )
        recent_event=DeviceEvent.objects.create(
            installation=self.device,event_type=DeviceEvent.Type.STARTUP_HEALTHY,
            occurred_at=timezone.now()-timedelta(days=1)
        )
        old_diag=DiagnosticRequest.objects.create(
            installation=self.device,status=DiagnosticRequest.Status.COMPLETED,completed_at=timezone.now()-timedelta(days=20)
        )
        DiagnosticRequest.objects.filter(pk=old_diag.pk).update(updated_at=timezone.now()-timedelta(days=11))
        pending=DiagnosticRequest.objects.create(
            installation=self.device,status=DiagnosticRequest.Status.PENDING,expires_at=timezone.now()+timedelta(days=1)
        )

        result=prune_operations_history()

        self.assertFalse(DeviceEvent.objects.filter(pk=old_event.pk).exists())
        self.assertTrue(DeviceEvent.objects.filter(pk=recent_event.pk).exists())
        self.assertFalse(DiagnosticRequest.objects.filter(pk=old_diag.pk).exists())
        self.assertTrue(DiagnosticRequest.objects.filter(pk=pending.pk).exists())
        self.assertGreaterEqual(result['events_deleted'],1)
        self.assertGreaterEqual(result['diagnostics_deleted'],1)
