from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import DeviceEvent, DiagnosticRequest


@shared_task
def prune_operations_history():
    now=timezone.now()
    event_days=max(7,int(getattr(settings,'CAF_INO_OPS_EVENT_RETENTION_DAYS',90)))
    diagnostic_days=max(1,int(getattr(settings,'CAF_INO_OPS_DIAGNOSTIC_RETENTION_DAYS',30)))
    events_deleted,_=DeviceEvent.objects.filter(occurred_at__lt=now-timedelta(days=event_days)).delete()
    diagnostics_deleted,_=DiagnosticRequest.objects.filter(
        status__in=[DiagnosticRequest.Status.COMPLETED,DiagnosticRequest.Status.EXPIRED,DiagnosticRequest.Status.CANCELLED],
        updated_at__lt=now-timedelta(days=diagnostic_days),
    ).delete()
    return {'events_deleted':events_deleted,'diagnostics_deleted':diagnostics_deleted}
