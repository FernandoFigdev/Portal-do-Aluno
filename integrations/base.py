"""Portas (interfaces) de integração com sistemas externos.

O restante do portal depende apenas destas abstrações. Para integrar um novo
sistema (ou o Cerbrum, quando houver API), cria-se um adapter e troca-se a
entrada correspondente em settings.INTEGRATIONS: nenhuma view precisa mudar.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


class IntegrationError(Exception):
    code = "integration_error"
    http_status = 502


class IntegrationUnavailable(IntegrationError):
    """Sistema externo indisponível ou integração não configurada (RF11, RN09)."""

    code = "integration_unavailable"
    http_status = 503


class StudentNotLinked(IntegrationError):
    """O aluno não possui identificador no sistema externo (risco 11.5 da ERS)."""

    code = "student_not_linked"
    http_status = 409

    def __init__(self, system: str):
        super().__init__(
            f"Seu cadastro ainda não está vinculado ao sistema '{system}'. "
            "Procure a secretaria."
        )
        self.system = system


@dataclass(frozen=True)
class CourseDTO:
    code: str
    name: str


@dataclass(frozen=True)
class GradeDTO:
    course_code: str
    course_name: str
    period: str
    value: str | None


@dataclass(frozen=True)
class MaterialDTO:
    course_code: str
    title: str
    url: str


class Provider(ABC):
    """Contrato comum. `system` é a chave em StudentProfile.external_ids."""

    system: str = ""
    label: str = ""

    def is_configured(self) -> bool:
        return True

    @abstractmethod
    def fetch(self, external_id: str) -> list:
        """Retorna DTOs do aluno ou levanta IntegrationUnavailable."""


class GradesProvider(Provider):
    """Notas (fonte: Cerbrum). Retorna list[GradeDTO]."""


class CoursesProvider(Provider):
    """Disciplinas. Retorna list[CourseDTO]."""


class MaterialsProvider(Provider):
    """Materiais (fonte: SECTRAS Online/Moodle). Retorna list[MaterialDTO]."""
