import mimetypes
import os

from django.http import FileResponse
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from core.permissions import IsSecretary, IsStudent

from .models import Certificate
from .serializers import AdminCertificateSerializer, CertificateSerializer


def _file_response(certificate):
    extension = os.path.splitext(certificate.file.name)[1]
    content_type = mimetypes.guess_type(f"x{extension}")[0] or "application/octet-stream"
    return FileResponse(
        certificate.file.open("rb"),
        as_attachment=True,
        filename=f"certificado-{certificate.pk}{extension}",
        content_type=content_type,
    )


class MyCertificateViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """'Meus Certificados' (RF21, RF23): somente os do aluno autenticado."""

    permission_classes = [IsStudent]
    serializer_class = CertificateSerializer

    def get_queryset(self):
        # RN02 / RN08 / RNF04: isolamento por dono no queryset
        return Certificate.objects.filter(student=self.request.user.student_profile)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        return _file_response(self.get_object())


class AdminCertificateViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin, viewsets.GenericViewSet,
):
    """Cadastro e correção de certificados pela secretaria (RF22, RF24)."""

    permission_classes = [IsSecretary]
    serializer_class = AdminCertificateSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = Certificate.objects.select_related("student__user", "uploaded_by")
        params = self.request.query_params
        if params.get("matricula"):
            qs = qs.filter(student__registration_number=params["matricula"])
        if params.get("categoria"):
            qs = qs.filter(category__iexact=params["categoria"])
        return qs

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        return _file_response(self.get_object())
