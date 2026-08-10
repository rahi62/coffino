from celery import shared_task

from .models import Notification
from .services import process_notification, process_pending


@shared_task
def deliver_notification(notification_id):
    """Send one persisted notification; retries are controlled by its queue state."""
    try:
        notification=Notification.objects.get(pk=notification_id)
    except Notification.DoesNotExist:
        return False
    process_notification(notification)
    return True


@shared_task
def process_pending_notifications():
    """Deliver queued notifications from the trusted background worker only."""
    return len(process_pending(limit=100, allow_global=True))
