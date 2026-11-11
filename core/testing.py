"""Utilitários compartilhados pelos testes."""
import shutil
import tempfile

from django.core.cache import cache
from django.test import override_settings

from accounts.models import StudentProfile, User

PDF_BYTES = b"%PDF-1.4\n%conteudo de teste\n%%EOF\n"
PASSWORD = "Senha@12345"


class PrivateMediaMixin:
    """Redireciona o armazenamento privado para um diretório temporário."""

    @classmethod
    def setUpClass(cls):
        cls._tmp_media = tempfile.mkdtemp()
        cls._media_override = override_settings(PRIVATE_MEDIA_ROOT=cls._tmp_media)
        cls._media_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._media_override.disable()
        shutil.rmtree(cls._tmp_media, ignore_errors=True)

    def setUp(self):
        cache.clear()
        super().setUp()


def make_student(username, first="Aluno", last="Teste", external_ids=None):
    user = User.objects.create_user(
        username=username, password=PASSWORD, first_name=first, last_name=last,
        role=User.Role.STUDENT,
    )
    StudentProfile.objects.create(
        user=user, registration_number=username, course="ADS",
        external_ids=external_ids or {},
    )
    return user


def make_secretary(username="secretaria", role=User.Role.STAFF):
    return User.objects.create_user(
        username=username, password=PASSWORD, first_name="Maria", last_name="Secretaria", role=role,
    )


# --- Providers falsos, usados apenas em testes (nunca em produção) ---------
from integrations.base import (  # noqa: E402
    CourseDTO, CoursesProvider, GradeDTO, GradesProvider, IntegrationUnavailable,
    MaterialDTO, MaterialsProvider,
)


class FakeCoursesProvider(CoursesProvider):
    system, label = "moodle", "SECTRAS Online"

    def fetch(self, external_id):
        return [CourseDTO(code="POO", name=f"POO (usuário {external_id})")]


class FakeGradesProvider(GradesProvider):
    system, label = "cerbrum", "Cerbrum"

    def fetch(self, external_id):
        return [GradeDTO("POO", "Programação OO", "2026.1", "8.5")]


class FakeMaterialsProvider(MaterialsProvider):
    system, label = "moodle", "SECTRAS Online"

    def fetch(self, external_id):
        raise IntegrationUnavailable("O SECTRAS Online está fora do ar.")


FAKE_INTEGRATIONS = {
    "grades": "core.testing.FakeGradesProvider",
    "courses": "core.testing.FakeCoursesProvider",
    "materials": "core.testing.FakeMaterialsProvider",
}
