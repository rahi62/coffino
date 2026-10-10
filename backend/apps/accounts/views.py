from django.db import IntegrityError
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import OtpChallenge
from .otp import OtpError, request_otp, verify_otp
from .otp_providers import OtpDeliveryError
from .registration import RegistrationError, register_saas_owner
from .serializers import RegistrationOtpRequestSerializer, OtpVerifySerializer, SaasRegistrationSerializer
from .throttles import OtpRequestThrottle, OtpVerifyThrottle, RegistrationThrottle


def _request_ip(request):
    return str(request.META.get("REMOTE_ADDR") or "")


@api_view(["POST"])
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
