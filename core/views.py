from django.db.models import Count
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuditLog
from .permissions import IsAdministrator
from .serializers import AuditLogSerializer


class DashboardView(APIView):
    """Painel inicial (RF04): somente o que o perfil autenticado pode ver."""

    def get(self, request):
        from certificates.models import Certificate
        from documents.models import DocumentRequest
        from integrations.services import get_shortcuts

        user = request.user
        statuses = {s: 0 for s in DocumentRequest.Status.values}

        if user.role == "STUDENT" and hasattr(user, "student_profile"):
            rows = (
                DocumentRequest.objects.filter(student=user.student_profile)
                .values("status").annotate(total=Count("id"))
            )
            for row in rows:
                statuses[row["status"]] = row["total"]
            return Response({
                "role": user.role,
                "requests": {"total": sum(statuses.values()), "by_status": statuses},
                "certificates": Certificate.objects.filter(student=user.student_profile).count(),
                "shortcuts": get_shortcuts(),
            })

        if user.is_secretary:
            rows = DocumentRequest.objects.values("status").annotate(total=Count("id"))
            for row in rows:
                statuses[row["status"]] = row["total"]
            open_states = ("RECEIVED", "IN_REVIEW", "AWAITING_INFO")
            return Response({
                "role": user.role,
                "requests": {
                    "total": sum(statuses.values()),
                    "open": sum(statuses[s] for s in open_states),
                    "by_status": statuses,
                },
                "certificates": Certificate.objects.count(),
                "shortcuts": get_shortcuts(),
            })

        return Response({"role": user.role, "shortcuts": get_shortcuts()})


class AuditLogListView(ListAPIView):
    """Consulta da trilha de auditoria (RF25). Somente administradores."""

    permission_classes = [IsAdministrator]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.select_related("actor")
        params = self.request.query_params
        for param, field in (("acao", "action"), ("tipo", "target_type"), ("alvo", "target_id")):
            if params.get(param):
                qs = qs.filter(**{field: params[param]})
        return qs
