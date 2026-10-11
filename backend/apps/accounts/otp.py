import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from .models import OtpChallenge
from .otp_providers import OtpDeliveryError, get_otp_sender
from .phone import mask_mobile, normalize_iran_mobile


class OtpError(ValueError):
    pass


class OtpCooldownError(OtpError):
    pass


class OtpInvalidError(OtpError):
    pass


class OtpRateLimitError(OtpError):
    pass


@dataclass(frozen=True)
class OtpRequestResult:
    challenge_id: UUID
    expires_at: datetime
    retry_after_seconds: int
    masked_mobile: str


@dataclass(frozen=True)
class VerifiedOtp:
    challenge_id: UUID
    mobile: str
    purpose: str
    user_id: int | None
    business_id: int | None


GRANT_SALT = "cafino.accounts.otp-verification.v1"


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _fingerprint(*parts: str) -> str:
    payload = "|".join(str(part or "") for part in parts).encode("utf-8")
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _rate_limit(key: str, *, limit: int, timeout: int = 3600):
    if cache.add(key, 1, timeout=timeout):
        return
    try:
        value = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=timeout)
        value = 1
    if value > limit:
        raise OtpRateLimitError("تعداد درخواست‌ها بیش از حد مجاز است. کمی بعد دوباره تلاش کنید.")


def _validate_purpose(purpose: str):
    if purpose not in OtpChallenge.Purpose.values:
        raise OtpInvalidError("درخواست کد یک‌بارمصرف معتبر نیست.")


def request_otp(*, mobile: str, purpose: str, user=None, business=None, request_ip: str = "") -> OtpRequestResult:
    _validate_purpose(purpose)
    normalized = normalize_iran_mobile(mobile)
    now = timezone.now()
    lock_key = f"cafino:otp:lock:{_fingerprint(normalized, purpose)}"
    if not cache.add(lock_key, 1, timeout=5):
        raise OtpCooldownError("کد به‌تازگی درخواست شده است. کمی صبر کنید.")

    try:
        with transaction.atomic():
            active = (
                OtpChallenge.objects.select_for_update()
                .filter(
                    mobile=normalized,
                    purpose=purpose,
                    business=business,
                    consumed_at__isnull=True,
                    verified_at__isnull=True,
                    expires_at__gt=now,
                )
                .order_by("-created_at")
                .first()
            )
            if active and active.next_send_at > now:
                raise OtpCooldownError("کد به‌تازگی ارسال شده است. کمی صبر کنید.")

            phone_key = _fingerprint("phone", normalized, purpose)
            ip_key = _fingerprint("ip", request_ip, purpose)
            limit = int(getattr(settings, "CAF_INO_OTP_SEND_LIMIT_PER_HOUR", 5))
            _rate_limit(f"cafino:otp:send:{phone_key}", limit=limit)
            if request_ip:
                _rate_limit(f"cafino:otp:send:{ip_key}", limit=limit * 4)

            code = generate_otp_code()
            ttl = int(getattr(settings, "CAF_INO_OTP_TTL_SECONDS", 300))
            resend = int(getattr(settings, "CAF_INO_OTP_RESEND_SECONDS", 60))
            max_attempts = int(getattr(settings, "CAF_INO_OTP_MAX_ATTEMPTS", 5))
            fingerprint = _fingerprint(normalized, request_ip, purpose)
            if active:
                active.code_hash = make_password(code)
                active.expires_at = now + timedelta(seconds=ttl)
                active.next_send_at = now + timedelta(seconds=resend)
                active.failed_attempts = 0
                active.max_attempts = max_attempts
                active.delivery_status = OtpChallenge.DeliveryStatus.PENDING
                active.provider_code = ""
                active.request_fingerprint = fingerprint
                active.user = user
                active.save()
                challenge = active
            else:
                challenge = OtpChallenge.objects.create(
                    mobile=normalized,
                    purpose=purpose,
                    code_hash=make_password(code),
                    expires_at=now + timedelta(seconds=ttl),
                    next_send_at=now + timedelta(seconds=resend),
                    max_attempts=max_attempts,
                    user=user,
                    business=business,
                    request_fingerprint=fingerprint,
                )

        try:
            delivery = get_otp_sender().send(
                mobile=normalized,
                code=code,
                correlation_id=str(challenge.correlation_id),
            )
        except Exception as exc:
            OtpChallenge.objects.filter(pk=challenge.pk).update(
                delivery_status=OtpChallenge.DeliveryStatus.FAILED,
                provider_code="",
                updated_at=timezone.now(),
            )
            if isinstance(exc, OtpDeliveryError):
                raise
            raise OtpDeliveryError("ارسال کد یک‌بارمصرف انجام نشد. کمی بعد دوباره تلاش کنید.") from exc

        OtpChallenge.objects.filter(pk=challenge.pk).update(
            delivery_status=OtpChallenge.DeliveryStatus.SENT,
            provider_code=delivery.provider_code[:64],
            updated_at=timezone.now(),
        )
        return OtpRequestResult(
            challenge_id=challenge.uuid,
            expires_at=challenge.expires_at,
            retry_after_seconds=resend,
            masked_mobile=mask_mobile(normalized),
        )
    finally:
        cache.delete(lock_key)


def verify_otp(*, challenge_id: UUID, code: str, expected_purpose: str, expected_business_id: int | None = None) -> str:
    _validate_purpose(expected_purpose)
    invalid_code = False
    grant = ""
    with transaction.atomic():
        try:
            challenge = OtpChallenge.objects.select_for_update().get(uuid=challenge_id)
        except (OtpChallenge.DoesNotExist, ValueError, TypeError) as exc:
            raise OtpInvalidError("کد واردشده معتبر یا قابل استفاده نیست.") from exc

        invalid_state = (
            challenge.purpose != expected_purpose
            or challenge.is_expired
            or challenge.is_consumed
            or challenge.verified_at is not None
            or challenge.is_locked
            or (expected_business_id is not None and challenge.business_id != expected_business_id)
        )
        if invalid_state:
            raise OtpInvalidError("کد واردشده معتبر یا قابل استفاده نیست.")
        if not check_password(str(code or ""), challenge.code_hash):
            challenge.failed_attempts += 1
            challenge.save(update_fields=["failed_attempts", "updated_at"])
            invalid_code = True
        else:
            challenge.verified_at = timezone.now()
            challenge.save(update_fields=["verified_at", "updated_at"])
            payload = {
                "challenge": str(challenge.uuid),
                "mobile": challenge.mobile,
                "purpose": challenge.purpose,
                "user_id": challenge.user_id,
                "business_id": challenge.business_id,
            }
            grant = signing.dumps(payload, salt=GRANT_SALT, compress=True)
    if invalid_code:
        raise OtpInvalidError("کد واردشده معتبر یا قابل استفاده نیست.")
    return grant


def consume_verification_grant(token: str, *, purpose: str, business_id: int | None = None) -> VerifiedOtp:
    _validate_purpose(purpose)
    try:
        payload = signing.loads(
            str(token or ""),
            salt=GRANT_SALT,
            max_age=int(getattr(settings, "CAF_INO_OTP_GRANT_TTL_SECONDS", 300)),
        )
    except signing.BadSignature as exc:
        raise OtpInvalidError("تأیید شماره همراه معتبر یا قابل استفاده نیست.") from exc

    if payload.get("purpose") != purpose:
        raise OtpInvalidError("تأیید شماره همراه معتبر یا قابل استفاده نیست.")
    if business_id is not None and payload.get("business_id") != business_id:
        raise OtpInvalidError("تأیید شماره همراه برای این کسب‌وکار معتبر نیست.")

    with transaction.atomic():
        try:
            challenge = OtpChallenge.objects.select_for_update().get(uuid=payload.get("challenge"))
        except (OtpChallenge.DoesNotExist, ValueError, TypeError) as exc:
            raise OtpInvalidError("تأیید شماره همراه معتبر یا قابل استفاده نیست.") from exc
        if (
            challenge.purpose != purpose
            or challenge.verified_at is None
            or challenge.is_consumed
            or challenge.is_expired
            or challenge.mobile != payload.get("mobile")
            or (business_id is not None and challenge.business_id != business_id)
        ):
            raise OtpInvalidError("تأیید شماره همراه معتبر یا قابل استفاده نیست.")
        challenge.consumed_at = timezone.now()
        challenge.save(update_fields=["consumed_at", "updated_at"])
        return VerifiedOtp(
            challenge_id=challenge.uuid,
            mobile=challenge.mobile,
            purpose=challenge.purpose,
            user_id=challenge.user_id,
            business_id=challenge.business_id,
        )
