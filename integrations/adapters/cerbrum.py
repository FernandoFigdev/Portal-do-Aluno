from integrations.base import GradesProvider, IntegrationUnavailable


class CerbrumGradesProvider(GradesProvider):
    """Ainda não há API oficial do Cerbrum confirmada.

    Falha de forma explícita em vez de inventar notas (RF11, RN09).
    Quando houver interface autorizada, implemente `fetch` aqui (ou crie um novo
    adapter e aponte GRADES_PROVIDER para ele).
    """

    system = "cerbrum"
    label = "Cerbrum"

    def is_configured(self) -> bool:
        return False

    def fetch(self, external_id: str):
        raise IntegrationUnavailable("A integração com o Cerbrum ainda não está disponível.")
