import requests
from django.conf import settings

from integrations.base import (
    CourseDTO,
    CoursesProvider,
    IntegrationUnavailable,
    MaterialDTO,
    MaterialsProvider,
)


class MoodleClient:
    """Cliente mínimo do Web Services REST do Moodle (SECTRAS Online).

    O token vai no corpo do POST (e não na URL) e nunca é registrado em logs ou
    mensagens de erro (ERS, seção 9).
    """

    def __init__(self):
        if not settings.MOODLE_BASE_URL or not settings.MOODLE_TOKEN:
            raise IntegrationUnavailable("A integração com o SECTRAS Online não está configurada.")
        self.url = settings.MOODLE_BASE_URL.rstrip("/") + "/webservice/rest/server.php"

    def call(self, function: str, **params):
        payload = {
            "wstoken": settings.MOODLE_TOKEN,
            "wsfunction": function,
            "moodlewsrestformat": "json",
            **params,
        }
        try:
            response = requests.post(self.url, data=payload, timeout=settings.INTEGRATION_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError):
            # `from None` evita vazar a URL/token em tracebacks
            raise IntegrationUnavailable(
                "Não foi possível consultar o SECTRAS Online no momento."
            ) from None
        if isinstance(data, dict) and "exception" in data:
            raise IntegrationUnavailable("O SECTRAS Online recusou a operação.") from None
        return data


class _MoodleBase:
    system = "moodle"
    label = "SECTRAS Online"

    def is_configured(self) -> bool:
        return bool(settings.MOODLE_BASE_URL and settings.MOODLE_TOKEN)


class MoodleCoursesProvider(_MoodleBase, CoursesProvider):
    def fetch(self, external_id: str):
        data = MoodleClient().call("core_enrol_get_users_courses", userid=external_id)
        return [CourseDTO(code=c.get("shortname", ""), name=c.get("fullname", "")) for c in data]


class MoodleMaterialsProvider(_MoodleBase, MaterialsProvider):
    def fetch(self, external_id: str):
        client = MoodleClient()
        materials = []
        for course in client.call("core_enrol_get_users_courses", userid=external_id):
            sections = client.call("core_course_get_contents", courseid=course["id"])
            for section in sections:
                for module in section.get("modules", []):
                    if module.get("url"):
                        materials.append(
                            MaterialDTO(
                                course_code=course.get("shortname", ""),
                                title=module.get("name", ""),
                                url=module["url"],
                            )
                        )
        return materials
