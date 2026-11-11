from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

from accounts.views import LoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/logout/", TokenBlacklistView.as_view(), name="logout"),
    path("api/", include("accounts.urls")),
    path("api/", include("core.urls")),
    path("api/", include("documents.urls")),
    path("api/", include("certificates.urls")),
    path("api/", include("integrations.urls")),
    path("api/", include("academic.urls")),
]