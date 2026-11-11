from django.urls import path

from .views import CoursesView, GradesView, MaterialsView

urlpatterns = [
    path("academico/disciplinas/", CoursesView.as_view(), name="academic-courses"),
    path("academico/notas/", GradesView.as_view(), name="academic-grades"),
    path("academico/materiais/", MaterialsView.as_view(), name="academic-materials"),
]
