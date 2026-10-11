from rest_framework.throttling import AnonRateThrottle, BaseThrottle


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



def request_client_ident(request) -> str:
    """Return the DRF client identifier using the configured trusted proxy count."""
    return BaseThrottle().get_ident(request)
