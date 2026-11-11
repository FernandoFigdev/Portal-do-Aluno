from django.http import FileResponse, Http404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsSecretary, IsStudent

from . import services
from .models import DocumentRequest, DocumentType
from .serializers import (
    AdminDocumentRequestSerializer,
    AdminDocumentTypeSerializer,
    DocumentRequestCreateSerializer,
    DocumentRequestSerializer,
    DocumentTypeSerializer,
    FileUploadSerializer,
    StatusChangeSerializer,
)

PROTOCOL_REGEX = r"[0-9A-Za-z\-]+"


def _pdf_response(request_obj):
    final = getattr(request_obj, "final_file", None)
    if final is None:
        raise Http404("Documento ainda não disponibilizado.")
    return FileResponse(
        final.file.open("rb"),
        as_attachment=True,
        filename=f"{request_obj.protocol}.pdf",
        content_type="application/pdf",
    )


class DocumentTypeListView(ListAPIView):
    """RF13: tipos de documento que podem ser solicitados."""

    permission_classes = [IsAuthenticated]
    serializer_class = DocumentTypeSerializer
    queryset = DocumentType.objects.filter(active=True)
    pagination_class = None


class MyDocumentRequestViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Solicitações do aluno autenticado (RF14, RF15, RF16, RF19)."""

    permission_classes = [IsStudent]
    lookup_field = "protocol"
    lookup_value_regex = PROTOCOL_REGEX

    def get_queryset(self):
        # RN02 / RNF04: o isolamento vive no queryset; protocolo alheio resulta em 404
        return (
            DocumentRequest.objects.filter(student=self.request.user.student_profile)
            .select_related("document_type", "final_file")
            .prefetch_related("history")
        )

    def get_serializer_class(self):
        return DocumentRequestCreateSerializer if self.action == "create" else DocumentRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = DocumentRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created = services.create_request(
            request.user.student_profile,
            serializer.validated_data["document_type"],
            serializer.validated_data.get("data", {}),
        )
        created = self.get_queryset().get(pk=created.pk)
        return Response(
            DocumentRequestSerializer(created, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="arquivo")
    def download(self, request, protocol=None):
        return _pdf_response(self.get_object())


class AdminDocumentTypeViewSet(viewsets.ModelViewSet):
    """Cadastro dos tipos de documento pela secretaria."""

    permission_classes = [IsSecretary]
    serializer_class = AdminDocumentTypeSerializer
    queryset = DocumentType.objects.all()
    pagination_class = None
    http_method_names = ["get", "post", "patch", "head", "options"]


class AdminDocumentRequestViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Gerenciamento de solicitações pela secretaria (RF17, RF18)."""

    permission_classes = [IsSecretary]
    serializer_class = AdminDocumentRequestSerializer
    lookup_field = "protocol"
    lookup_value_regex = PROTOCOL_REGEX

    def get_queryset(self):
        qs = DocumentRequest.objects.select_related(
            "student__user", "document_type", "final_file"
        ).prefetch_related("history__changed_by")
        params = self.request.query_params
        if params.get("status") in DocumentRequest.Status.values:
            qs = qs.filter(status=params["status"])
        if params.get("protocolo"):
            qs = qs.filter(protocol__icontains=params["protocolo"])
        if params.get("matricula"):
            qs = qs.filter(student__registration_number=params["matricula"])
        if params.get("tipo", "").isdigit():
            qs = qs.filter(document_type_id=int(params["tipo"]))
        return qs

    def _fresh(self, request_obj):
        return self.get_queryset().get(pk=request_obj.pk)

    @action(detail=True, methods=["patch"], url_path="estado")
    def estado(self, request, protocol=None):
        obj = self.get_object()
        serializer = StatusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.change_status(
            obj, serializer.validated_data["status"], request.user,
            serializer.validated_data.get("note", ""),
        )
        return Response(self.get_serializer(self._fresh(obj)).data)

    @action(
        detail=True, methods=["get", "post"], url_path="arquivo",
        parser_classes=[MultiPartParser, FormParser, JSONParser],
    )
    def arquivo(self, request, protocol=None):
        obj = self.get_object()
        if request.method == "GET":
            return _pdf_response(obj)
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.attach_final_file(obj, serializer.validated_data["file"], request.user)
        return Response(
            self.get_serializer(self._fresh(obj)).data, status=status.HTTP_201_CREATED
        )
