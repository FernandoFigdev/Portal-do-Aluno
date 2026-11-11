from .models import AuditLog

_FORBIDDEN = ("password", "senha", "token", "secret", "authorization", "credential")


def _sanitize(value):
    if isinstance(value, dict):
        return {
            k: _sanitize(v)
            for k, v in value.items()
            if not any(word in str(k).lower() for word in _FORBIDDEN)
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize(v) for v in value]
    return value


def audit(actor, action: str, target, details: dict | None = None) -> AuditLog:
    """Grava uma ação administrativa, descartando qualquer chave sensível."""
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        target_type=target.__class__.__name__,
        target_id=str(target.pk),
        details=_sanitize(details or {}),
    )
