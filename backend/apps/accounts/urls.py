from django.urls import path

from . import views


urlpatterns = [
    path("password/forgot/", views.password_forgot, name="password-forgot"),
    path("password/otp/verify/", views.password_otp_verify, name="password-otp-verify"),
    path("password/reset/", views.password_reset, name="password-reset"),
    path("login/otp/request/", views.login_otp_request, name="login-otp-request"),
    path("login/otp/verify/", views.login_otp_verify, name="login-otp-verify"),
    path("register/otp/request/", views.registration_otp_request, name="registration-otp-request"),
    path("register/otp/verify/", views.registration_otp_verify, name="registration-otp-verify"),
    path("register/", views.register, name="saas-register"),
]
