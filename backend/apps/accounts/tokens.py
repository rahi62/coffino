from datetime import UTC, datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken



TOKEN_REVOKED_MESSAGE = "نشست شما منقضی یا باطل شده است؛ دوباره وارد شوید."


def issue_token_pair(user) -> dict[str, str]:
    if not user or not user.is_active:
        raise AuthenticationFailed("حساب کاربری فعال نیست.")
    refresh = RefreshToken.for_user(user)
    refresh["auth_time"] = timezone.now().timestamp()
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


def token_precedes_invalidation(token, user) -> bool:
    cutoff = getattr(user, "tokens_invalid_before", None)
    issued_at = token.get("auth_time", token.get("iat"))
    if cutoff is None:
        return False
    if issued_at is None:
        return True
    return datetime.fromtimestamp(float(issued_at), tz=UTC) < cutoff


class CafinoTokenObtainPairSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "نام کاربری یا گذرواژه نادرست است.",
    }

    def validate(self, attrs):
        super().validate(attrs)
        return issue_token_pair(self.user)


class CafinoTokenRefreshSerializer(TokenRefreshSerializer):
    default_error_messages = {
        "no_active_account": TOKEN_REVOKED_MESSAGE,
    }

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])
        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        if not user_id:
            raise AuthenticationFailed(TOKEN_REVOKED_MESSAGE, code="token_not_valid")
        User = get_user_model()
        try:
            user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except User.DoesNotExist as exc:
            raise AuthenticationFailed(TOKEN_REVOKED_MESSAGE, code="user_not_found") from exc
        if not api_settings.USER_AUTHENTICATION_RULE(user):
            raise AuthenticationFailed(TOKEN_REVOKED_MESSAGE, code="no_active_account")
        if token_precedes_invalidation(refresh, user):
            raise AuthenticationFailed(TOKEN_REVOKED_MESSAGE, code="token_revoked")
        return super().validate(attrs)


