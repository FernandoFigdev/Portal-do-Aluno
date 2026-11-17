from django.urls import path

from .views import IntegrationStatusView, ShortcutsView

urlpatterns = [
    path("integracoes/status/", IntegrationStatusView.as_view(), name="integration-status"),
    path("integracoes/atalhos/", ShortcutsView.as_view(), name="integration-shortcuts"),
]
