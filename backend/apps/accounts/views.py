from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import OtpChallenge, User
from .otp import OtpError, consume_verification_grant, request_otp, verify_otp
from .phone import mask_mobile
from .tokens import issue_token_pair
from .otp_providers import OtpDeliveryError
from .registration import RegistrationError, register_saas_owner
from .recovery import PasswordRecoveryError, request_password_recovery, reset_password_with_grant
from .serializers import (
    RegistrationOtpRequestSerializer,
    OtpVerifySerializer,
    SaasRegistrationSerializer,
    PasswordRecoveryRequestSerializer,
    PasswordResetSerializer,
)
from .throttles import OtpRequestThrottle, OtpVerifyThrottle, RegistrationThrottle, PasswordRecoveryThrottle


def _request_ip(request):
    return str(request.META.get("REMOTE_ADDR") or "")


@api_view(["POST"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
@throttle_classes([OtpRequestThrottle])
def registration_otp_request(request):
    serializer = RegistrationOtpRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        result = request_otp(
            mobile=serializer.validated_data["mobile"],
            purpose=OtpChallenge.Purpose.SAAS_REGISTRATION,
            request_ip=_request_ip(request),
        )
    except (OtpError, OtpDeliveryError) as exc:
        raise ValidationError({"detail": str(exc)}) from exc
    return Response(
        {
            "detail": "کد تأیید ارسال شد.",
            "challenge_id": result.challenge_id,
            "expires_at": result.expires_at,
            "retry_after_seconds": result.retry_after_seconds,
            "mobile": result.masked_mobile,
        }
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
@throttle_classes([OtpVerifyThrottle])
def registration_otp_verify(request):
    serializer = OtpVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        grant = verify_otp(
            challenge_id=serializer.validated_data["challenge_id"],
            code=serializer.validated_data["code"],
            expected_purpose=OtpChallenge.Purpose.SAAS_REGISTRATION,
        )
    except OtpError as exc:
        raise ValidationError({"detail": str(exc)}) from exc
    return Response({"detail": "شماره همراه تأیید شد.", "verification_grant": grant})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
@throttle_classes([RegistrationThrottle])
def register(request):
    serializer = SaasRegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        result = register_saas_owner(
            business_name=data["business_name"],
            business_type=data["business_type"],
            branch_name=data["branch_name"],
            branch_phone=data["branch_phone"],
            copy_owner_mobile_to_branch=data["copy_owner_mobile_to_branch"],
            username=data["username"],
            email=data["email"],
            password=data["password"],
            verification_grant=data["verification_grant"],
        )
    except RegistrationError as exc:
        raise ValidationError({"detail": str(exc)}) from exc
    except IntegrityError as exc:
        raise ValidationError(
            {"detail": "اطلاعات حساب با یک ثبت‌نام موجود تداخل دارد. دوباره بررسی کنید."}
        ) from exc
    return Response(
        {
            "user": {"id": result.user.id, "username": result.user.username, "email": result.user.email},
            "business": {"id": result.business.id, "name": result.business.name},
            "branch": {"id": result.branch.id, "name": result.branch.name},
            "next": "onboarding",
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
@throttle_classes([OtpRequestThrottle])
def login_otp_request(request):
    serializer = RegistrationOtpRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    mobile = serializer.validated_data["mobile"]
    users = list(User.objects.filter(
        mobile=mobile, mobile_verified_at__isnull=False, is_active=True,
    )[:2])
    result = None
    if len(users) == 1:
        try:
            result = request_otp(
                mobile=mobile, purpose=OtpChallenge.Purpose.STAFF_LOGIN,
                user=users[0], business=users[0].business, request_ip=_request_ip(request),
            )
        except (OtpError, OtpDeliveryError):
            # Keep response status and shape identical for absent and existing accounts.
            pass
    return Response({
        "detail": "اگر حساب فعالی با این شماره وجود داشته باشد، کد ورود ارسال می‌شود.",
        "challenge_id": result.challenge_id if result else uuid4(),
        "expires_at": result.expires_at if result else timezone.now() + timedelta(seconds=settings.CAF_INO_OTP_TTL_SECONDS),
        "retry_after_seconds": settings.CAF_INO_OTP_RESEND_SECONDS,
        "mobile": mask_mobile(mobile),
    })


@api_view(["POST"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
@throttle_classes([OtpVerifyThrottle])
def login_otp_verify(request):
    serializer = OtpVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        # Verification commits failed attempts even when the caller receives an error.
        grant = verify_otp(
            challenge_id=serializer.validated_data["challenge_id"],
            code=serializer.validated_data["code"],
            expected_purpose=OtpChallenge.Purpose.STAFF_LOGIN,
        )
        with transaction.atomic():
            verified = consume_verification_grant(grant, purpose=OtpChallenge.Purpose.STAFF_LOGIN)
            user = User.objects.select_for_update().get(
                pk=verified.user_id, mobile=verified.mobile,
                mobile_verified_at__isnull=False, is_active=True,
            )
            pair = issue_token_pair(user)
    except (OtpError, User.DoesNotExist) as exc:
        raise ValidationError({"detail": "کد ورود معتبر یا قابل استفاده نیست."}) from exc
    return Response(pair)



@api_view(["POST"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
@throttle_classes([PasswordRecoveryThrottle])
def password_forgot(request):
    serializer = PasswordRecoveryRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    result = request_password_recovery(
        identifier=serializer.validated_data["identifier"],
        request_ip=_request_ip(request),
    )
    otp = result.otp
    return Response({
        "detail": "اگر حساب فعالی با این مشخصات وجود داشته باشد، راهنمای بازیابی ارسال می‌شود.",
        "challenge_id": otp.challenge_id if otp else uuid4(),
        "expires_at": otp.expires_at if otp else timezone.now() + timedelta(seconds=settings.CAF_INO_OTP_TTL_SECONDS),
        "retry_after_seconds": settings.CAF_INO_OTP_RESEND_SECONDS,
    })


@api_view(["POST"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
@throttle_classes([PasswordRecoveryThrottle])
def password_otp_verify(request):
    serializer = OtpVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        grant = verify_otp(
            challenge_id=serializer.validated_data["challenge_id"],
            code=serializer.validated_data["code"],
            expected_purpose=OtpChallenge.Purpose.PASSWORD_RECOVERY,
        )
    except OtpError as exc:
        raise ValidationError({"detail": "کد بازیابی معتبر یا قابل استفاده نیست."}) from exc
    return Response({"detail": "کد بازیابی تأیید شد.", "verification_grant": grant})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
@throttle_classes([PasswordRecoveryThrottle])
def password_reset(request):
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        reset_password_with_grant(
            verification_grant=serializer.validated_data["verification_grant"],
            password=serializer.validated_data["password"],
        )
    except PasswordRecoveryError as exc:
        raise ValidationError({"detail": str(exc)}) from exc
    return Response({"ok": True, "detail": "گذرواژه با موفقیت تغییر کرد. دوباره وارد شوید."})
