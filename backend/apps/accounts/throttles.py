from rest_framework.throttling import ScopedRateThrottle


class RegistrationThrottle(ScopedRateThrottle):
    scope = "auth_registration"


class AuthLoginThrottle(ScopedRateThrottle):
    scope = "auth_login"


class OtpRequestThrottle(ScopedRateThrottle):
    scope = "auth_otp_request"


class OtpVerifyThrottle(ScopedRateThrottle):
    scope = "auth_otp_verify"


class PasswordRecoveryThrottle(ScopedRateThrottle):
    scope = "auth_recovery"
