from django.conf import settings

from .base import IntegrationUnavailable, StudentNotLinked
from .models import IntegrationLog
from .registry import KINDS, get_provider


def _log(system, operation, success, message=""):
    IntegrationLog.objects.create(
        system=system, operation=operation, success=success, message=message[:255]
    )


def fetch_for_student(kind: str, student):
    """Consulta o sistema externo para um aluno, registrando o resultado.

    Retorna (provider, dados). Nunca devolve dados simulados: se a fonte estiver
    indisponível, levanta IntegrationUnavailable (RN09).
    """
    provider = get_provider(kind)

    if not provider.is_configured():
        _log(provider.system, kind, False, "Integração não configurada.")
        raise IntegrationUnavailable(
            f"A integração com {provider.label or provider.system} ainda não está disponível."
        )

    external_id = (student.external_ids or {}).get(provider.system)
    if not external_id:
        _log(provider.system, kind, False, "Aluno sem vínculo no sistema externo.")
        raise StudentNotLinked(provider.label or provider.system)

    try:
        data = provider.fetch(str(external_id))
    except IntegrationUnavailable as exc:
        _log(provider.system, kind, False, str(exc))
        raise

    _log(provider.system, kind, True)
    return provider, data


def get_shortcuts():
    """Atalhos para os sistemas existentes (RF09)."""
    links = (
        ("cerbrum", "Cerbrum", settings.CERBRUM_URL),
        ("sectras", "SECTRAS Online", settings.SECTRAS_URL),
    )
    return [{"key": k, "name": n, "url": u} for k, n, u in links if u]


def get_status():
    """Estado de cada integração, sem chamar o sistema externo."""
    result = []
    for kind in KINDS:
        provider = get_provider(kind)
        last = IntegrationLog.objects.filter(system=provider.system, operation=kind).first()
        result.append({
            "service": kind,
            "system": provider.system,
            "name": provider.label or provider.system,
            "configured": provider.is_configured(),
            "last_check": None if last is None else {
                "success": last.success,
                "at": last.created_at.isoformat(),
                "message": last.message,
            },
        })
    return result
