from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.permissions import has_perm
from apps.businesses.models import Business
from apps.core.tenancy import tenant_business
from apps.core.settings_readiness import settings_readiness_payload


@api_view(['GET'])
def settings_readiness(request):
    if not has_perm(request.user, 'settings.manage'):
        return Response({'detail': 'دسترسی به تنظیمات ندارید'}, status=403)

    if request.user.is_superuser:
        business = request.user.business if request.user.business_id else None
        if request.query_params.get('business'):
            business = get_object_or_404(Business, pk=request.query_params.get('business'))
    else:
        business = tenant_business(request.user)

    if business is None:
        return Response({'detail': 'کسب‌وکار برای تنظیمات مشخص نیست'}, status=400)

    return Response(settings_readiness_payload(business))
