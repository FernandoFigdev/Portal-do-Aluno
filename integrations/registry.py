from django.conf import settings
from django.utils.module_loading import import_string

KINDS = ("grades", "courses", "materials")


def get_provider(kind: str):
    """Ponto único que decide qual implementação atende cada serviço.

    Lê settings.INTEGRATIONS (caminhos pontilhados), portanto trocar o Cerbrum
    "stub" por uma integração real é uma mudança de configuração.
    """
    path = settings.INTEGRATIONS[kind]
    return import_string(path)()
