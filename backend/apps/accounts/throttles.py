from rest_framework.throttling import AnonRateThrottle


class RegistrationThrottle(AnonRateThrottle):
    scope = "auth_registration"


class AuthLoginThrottle(AnonRateThrottle):
    scope = "auth_login"


class OtpRequestThrottle(AnonRateThrottle):
    scope = "auth_otp_request"


class OtpVerifyThrottle(AnonRateThrottle):
    scope = "auth_otp_verify"


class PasswordRecoveryThrottle(AnonRateThrottle):
    scope = "auth_recovery"
