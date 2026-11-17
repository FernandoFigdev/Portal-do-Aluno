from rest_framework.generics import RetrieveAPIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import MeSerializer


class LoginView(TokenObtainPairView):
    """Login (RF01) com limite de tentativas contra força bruta."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class MeView(RetrieveAPIView):
    """Dados do usuário autenticado (RF04/RF05)."""

    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user
