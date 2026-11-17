from rest_framework.response import Response
from rest_framework.views import APIView

from .services import get_shortcuts, get_status


class IntegrationStatusView(APIView):
    """RF11: informa quais integrações estão configuradas e o último resultado."""

    def get(self, request):
        return Response(get_status())


class ShortcutsView(APIView):
    """RF09: atalhos para o Cerbrum e o SECTRAS Online."""

    def get(self, request):
        return Response(get_shortcuts())
