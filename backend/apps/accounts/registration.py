from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.businesses.models import Branch, Business

from .models import OtpChallenge, User
from .otp import OtpInvalidError, consume_verification_grant
from .passwords import OwnerPasswordError, validate_owner_password


class RegistrationError(ValueError):
    pass


@dataclass(frozen=True)
class RegistrationResult:
    user: User
    business: Business
    branch: Branch


@transaction.atomic
def register_saas_owner(
    *,
    business_name: str,
    business_type: str,
    branch_name: str,
    branch_phone: str,
    copy_owner_mobile_to_branch: bool,
    username: str,
    email: str,
    password: str,
    verification_grant: str,
) -> RegistrationResult:
    try:
        verified = consume_verification_grant(
            verification_grant,
            purpose=OtpChallenge.Purpose.SAAS_REGISTRATION,
        )
    except OtpInvalidError as exc:
        raise RegistrationError("تأیید شماره همراه معتبر نیست یا قبلاً استفاده شده است.") from exc

    if User.objects.filter(username__iexact=username).exists():
        raise RegistrationError("این نام کاربری قبلاً ثبت شده است.")
    if email and User.objects.filter(email__iexact=email).exists():
        raise RegistrationError("این ایمیل قبلاً ثبت شده است.")
    if User.objects.filter(mobile=verified.mobile).exists():
        raise RegistrationError("این شماره همراه قبلاً برای حساب دیگری ثبت شده است.")

    candidate = User(
        username=username,
        email=email,
        mobile=verified.mobile,
        role=User.Role.OWNER,
        is_active=True,
    )
    try:
        validate_owner_password(password, user=candidate, business_name=business_name)
    except OwnerPasswordError as exc:
        raise RegistrationError(str(exc)) from exc

    business = Business.objects.create(
        name=business_name,
        business_type=business_type,
        deployment_type="SAAS",
        is_active=True,
    )
    resolved_branch_phone = verified.mobile if copy_owner_mobile_to_branch else branch_phone
    branch = Branch.objects.create(
        business=business,
        name=branch_name,
        phone=resolved_branch_phone,
        is_active=True,
    )
    owner = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        mobile=verified.mobile,
        mobile_verified_at=timezone.now(),
        business=business,
        branch=None,
        role=User.Role.OWNER,
        is_active=True,
    )
    return RegistrationResult(user=owner, business=business, branch=branch)
