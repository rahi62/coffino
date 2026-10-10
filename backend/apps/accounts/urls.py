from django.urls import path

from . import views


urlpatterns = [
    path("register/otp/request/", views.registration_otp_request, name="registration-otp-request"),
    path("register/otp/verify/", views.registration_otp_verify, name="registration-otp-verify"),
    path("register/", views.register, name="saas-register"),
]
