from rest_framework.routers import SimpleRouter

from .views import AdminCertificateViewSet, MyCertificateViewSet

router = SimpleRouter()
router.register("certificados", MyCertificateViewSet, basename="my-certificates")
router.register("admin/certificados", AdminCertificateViewSet, basename="admin-certificates")

urlpatterns = router.urls
