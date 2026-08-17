from django.urls import path

from . import views

urlpatterns=[
    path('register/',views.device_register,name='ops-device-register'),
    path('heartbeat/',views.device_heartbeat,name='ops-device-heartbeat'),
    path('policy/',views.device_policy,name='ops-device-policy'),
    path('events/',views.device_event,name='ops-device-event'),
    path('diagnostics/',views.device_diagnostic_submit,name='ops-device-diagnostic-submit'),
]
