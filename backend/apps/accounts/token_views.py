from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .throttles import AuthLoginThrottle
from .tokens import CafinoTokenObtainPairSerializer, CafinoTokenRefreshSerializer


class CafinoTokenObtainPairView(TokenObtainPairView):
    serializer_class = CafinoTokenObtainPairSerializer
    throttle_classes = [AuthLoginThrottle]


class CafinoTokenRefreshView(TokenRefreshView):
    serializer_class = CafinoTokenRefreshSerializer
