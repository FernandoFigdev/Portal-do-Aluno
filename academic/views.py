from dataclasses import asdict

from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsStudent
from integrations.services import fetch_for_student

from .sqlite_service import (
    listar_disciplinas,
    listar_notas,
)

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



class SQLiteAcademicView(APIView):
    permission_classes = [IsStudent]

    def consultar(self, matricula):
        raise NotImplementedError

    def get(self, request):
        matricula = (
            request.user.student_profile.registration_number
        )

        return Response({
            "source": "SQLite Acadêmico",
            "fetched_at": timezone.now().isoformat(),
            "results": self.consultar(matricula),
        })


class CoursesView(SQLiteAcademicView):
    def consultar(self, matricula):
        return listar_disciplinas(matricula)


class GradesView(SQLiteAcademicView):
    def consultar(self, matricula):
        return listar_notas(matricula)


class MaterialsView(ExternalDataView):
    kind = "materials"
