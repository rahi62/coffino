from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from .tokens import TOKEN_REVOKED_MESSAGE, token_precedes_invalidation


class CafinoJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if token_precedes_invalidation(validated_token, user):
            raise AuthenticationFailed(TOKEN_REVOKED_MESSAGE, code="token_revoked")
        return user
