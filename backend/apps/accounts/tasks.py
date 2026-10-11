from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .models import OtpChallenge


@shared_task
def prune_otp_challenges():
    cutoff = timezone.now() - timedelta(
        days=int(getattr(settings, "CAF_INO_OTP_RETENTION_DAYS", 7))
    )
    deleted, _ = OtpChallenge.objects.filter(
        Q(expires_at__lt=cutoff) | Q(consumed_at__lt=cutoff)
    ).delete()
    return deleted
