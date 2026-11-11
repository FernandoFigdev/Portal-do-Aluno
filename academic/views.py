from dataclasses import asdict

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsStudent
from integrations.services import fetch_for_student


class ExternalDataView(APIView):
    """Base: consulta uma fonte externa para o aluno autenticado (RF05 a RF08).

    O aluno é sempre o usuário autenticado: não há parâmetro de ID (RN02).
    """

    permission_classes = [IsStudent]
    kind = ""

    def get(self, request):
        provider, data = fetch_for_student(self.kind, request.user.student_profile)
        return Response({
            "source": provider.label or provider.system,
            "fetched_at": timezone.now().isoformat(),
            "results": [asdict(item) for item in data],
        })


class CoursesView(ExternalDataView):
    kind = "courses"


class GradesView(ExternalDataView):
    kind = "grades"


class MaterialsView(ExternalDataView):
    kind = "materials"
