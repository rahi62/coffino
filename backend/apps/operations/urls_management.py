from django.urls import path

from . import views

urlpatterns=[
    path('summary/',views.management_summary,name='ops-management-summary'),
    path('devices/',views.management_devices,name='ops-management-devices'),
    path('devices/<int:pk>/assign/',views.management_assign_device,name='ops-management-assign'),
    path('devices/<int:pk>/diagnostics/',views.management_diagnostics,name='ops-management-diagnostics'),
    path('devices/<int:pk>/diagnostics/request/',views.management_request_diagnostic,name='ops-management-diagnostic-request'),
    path('policies/',views.management_policies,name='ops-management-policies'),
    path('policies/<str:channel>/',views.management_policy_detail,name='ops-management-policy-detail'),
]
