from django.urls import path

from .views import AuditLogListView, DashboardView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("admin/auditoria/", AuditLogListView.as_view(), name="audit-log"),
]
