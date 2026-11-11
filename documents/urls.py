from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    AdminDocumentRequestViewSet,
    AdminDocumentTypeViewSet,
    DocumentTypeListView,
    MyDocumentRequestViewSet,
)

router = SimpleRouter()
router.register("documentos/solicitacoes", MyDocumentRequestViewSet, basename="my-requests")
router.register("admin/solicitacoes", AdminDocumentRequestViewSet, basename="admin-requests")
router.register("admin/tipos-documento", AdminDocumentTypeViewSet, basename="admin-document-types")

urlpatterns = [
    path("documentos/tipos/", DocumentTypeListView.as_view(), name="document-types"),
] + router.urls
