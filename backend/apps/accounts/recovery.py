from dataclasses import dataclass

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from .models import OtpChallenge, User
from .otp import OtpError, OtpInvalidError, OtpRequestResult, consume_verification_grant, request_otp
from .otp_providers import OtpDeliveryError
from .passwords import OwnerPasswordError, validate_owner_password
from .phone import normalize_iran_mobile


class PasswordRecoveryError(ValueError):
    pass


@dataclass(frozen=True)
class PasswordRecoveryRequestResult:
    otp: OtpRequestResult | None


def resolve_recovery_user(identifier: str) -> User | None:
    value = str(identifier or "").strip()
    if not value:
        return None

    try:
        mobile = normalize_iran_mobile(value)
    except DjangoValidationError:
        mobile = ""

    if mobile:
        rows = list(
            User.objects.filter(
                mobile=mobile,
                mobile_verified_at__isnull=False,
                is_active=True,
            ).order_by("id")[:2]
        )
        return rows[0] if len(rows) == 1 else None

    username_rows = list(
        User.objects.filter(username=value, is_active=True).order_by("id")[:2]
    )
    if len(username_rows) == 1:
        return username_rows[0]

    email_rows = list(
        User.objects.filter(email__iexact=value, is_active=True)
        .exclude(email="")
        .order_by("id")[:2]
    )
    return email_rows[0] if len(email_rows) == 1 else None


def request_password_recovery(*, identifier: str, request_ip: str = "") -> PasswordRecoveryRequestResult:
    user = resolve_recovery_user(identifier)
    if not user or not user.mobile or user.mobile_verified_at is None:
        return PasswordRecoveryRequestResult(otp=None)

    try:
        otp = request_otp(
            mobile=user.mobile,
            purpose=OtpChallenge.Purpose.PASSWORD_RECOVERY,
            user=user,
            business=user.business,
            request_ip=request_ip,
        )
    except (OtpError, OtpDeliveryError):
        # Enumeration safety: callers always receive the same public response.
        return PasswordRecoveryRequestResult(otp=None)
    return PasswordRecoveryRequestResult(otp=otp)


@transaction.atomic
def reset_password_with_grant(*, verification_grant: str, password: str) -> User:
    try:
        verified = consume_verification_grant(
            verification_grant,
            purpose=OtpChallenge.Purpose.PASSWORD_RECOVERY,
        )
    except OtpInvalidError as exc:
        raise PasswordRecoveryError("درخواست بازیابی معتبر یا قابل استفاده نیست.") from exc

    if not verified.user_id:
        raise PasswordRecoveryError("درخواست بازیابی معتبر یا قابل استفاده نیست.")

    try:
        user = User.objects.select_for_update().get(
            pk=verified.user_id,
            mobile=verified.mobile,
            mobile_verified_at__isnull=False,
            is_active=True,
        )
    except User.DoesNotExist as exc:
        raise PasswordRecoveryError("درخواست بازیابی معتبر یا قابل استفاده نیست.") from exc

    business_name = user.business.name if user.business_id and user.business else ""
    try:
        validate_owner_password(password, user=user, business_name=business_name)
    except OwnerPasswordError as exc:
        raise PasswordRecoveryError(str(exc)) from exc

    now = timezone.now()
    user.set_password(password)
    user.tokens_invalid_before = now
    user.save(update_fields=["password", "tokens_invalid_before"])
    OtpChallenge.objects.filter(
        user=user,
        purpose=OtpChallenge.Purpose.PASSWORD_RECOVERY,
        consumed_at__isnull=True,
    ).update(consumed_at=now, updated_at=now)
    return user
