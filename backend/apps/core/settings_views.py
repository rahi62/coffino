from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.permissions import has_perm
from apps.businesses.models import Business
from apps.core.go_live import deployment_profiles_payload, go_live_payload
from apps.core.onboarding import apply_onboarding_preset, onboarding_presets_payload
from apps.core.settings_health import printer_runtime_health_payload, settings_health_payload
from apps.core.settings_readiness import settings_readiness_payload
from apps.core.tenancy import resolve_branch_for_user, tenant_business


def _settings_business(request, explicit_business=None):
    if request.user.is_superuser:
        business = request.user.business if request.user.business_id else None
        business_id = explicit_business or request.query_params.get('business')
        if business_id:
            business = get_object_or_404(Business, pk=business_id)
    else:
        business = tenant_business(request.user)
    return business


def _require_settings(request):
    return has_perm(request.user, 'settings.manage')


def _require_onboarding(request):
    # Applying a preset changes Business type/deployment and module activation, not just
    # branch-local settings. Keep that power behind the business-management boundary.
    return _require_settings(request) and has_perm(request.user, 'business.manage')


@api_view(['GET'])
def settings_readiness(request):
    if not _require_settings(request):
        return Response({'detail': 'دسترسی به تنظیمات ندارید'}, status=403)
    business = _settings_business(request)
    if business is None:
        return Response({'detail': 'کسب‌وکار برای تنظیمات مشخص نیست'}, status=400)
    return Response(settings_readiness_payload(business))


@api_view(['GET'])
def settings_onboarding_presets(request):
    if not _require_onboarding(request):
        return Response({'detail': 'دسترسی مدیریت کسب‌وکار برای راه‌اندازی لازم است'}, status=403)
    return Response(onboarding_presets_payload())


@api_view(['POST'])
def settings_onboarding_apply(request):
    if not _require_onboarding(request):
        return Response({'detail': 'دسترسی مدیریت کسب‌وکار برای راه‌اندازی لازم است'}, status=403)
    business = _settings_business(request, request.data.get('business'))
    if business is None:
        return Response({'detail': 'کسب‌وکار برای راه‌اندازی مشخص نیست'}, status=400)
    try:
        result = apply_onboarding_preset(
            business=business,
            actor=request.user,
            payload=request.data,
            request=request,
        )
    except ValueError as error:
        return Response({'detail': str(error)}, status=400)
    return Response(result)


@api_view(['GET'])
def settings_health(request):
    if not _require_settings(request):
        return Response({'detail': 'دسترسی به Health Check ندارید'}, status=403)
    try:
        branch = resolve_branch_for_user(request.user, request.query_params.get('branch'))
    except Exception:
        return Response({'detail': 'شعبه Health Check معتبر یا مجاز نیست'}, status=403)
    live = str(request.query_params.get('live') or '').lower() in ['1', 'true', 'yes', 'on']
    return Response(settings_health_payload(branch, live=live))


@api_view(['POST'])
def settings_printer_health(request):
    if not _require_settings(request):
        return Response({'detail': 'دسترسی به Health Check ندارید'}, status=403)
    try:
        branch = resolve_branch_for_user(request.user, request.data.get('branch'))
    except Exception:
        return Response({'detail': 'شعبه Health Check معتبر یا مجاز نیست'}, status=403)
    devices = request.data.get('devices')
    if not isinstance(devices, list):
        return Response({'detail': 'فهرست دستگاه‌های پرینتر نامعتبر است'}, status=400)
    return Response(printer_runtime_health_payload(branch, devices))


@api_view(['GET'])
def settings_deployment_profiles(request):
    if not _require_settings(request):
        return Response({'detail': 'دسترسی به Deployment Profile ندارید'}, status=403)
    return Response(deployment_profiles_payload())


@api_view(['GET'])
def settings_go_live(request):
    if not _require_settings(request):
        return Response({'detail': 'دسترسی به Go-Live Guard ندارید'}, status=403)
    business = _settings_business(request)
    if business is None:
        return Response({'detail': 'کسب‌وکار برای Go-Live مشخص نیست'}, status=400)
    return Response(go_live_payload(business))
