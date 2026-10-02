from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .admin_localization import localized_text, localize_admin
from . import admin_localization_extra  # noqa: F401 - extends runtime localization maps before applying them

admin.site.site_header=localized_text('مدیریت کافینو', 'Cafino Administration')
admin.site.site_title=localized_text('مدیریت کافینو', 'Cafino Administration')
admin.site.index_title=localized_text('مدیریت سامانهٔ کافینو', 'Cafino Administration')
localize_admin()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/ops/v1/", include("apps.operations.urls_device")),
    path("api/v1/operations/", include("apps.operations.urls_management")),
    path("api/v1/", include("apps.core.urls")),
]
