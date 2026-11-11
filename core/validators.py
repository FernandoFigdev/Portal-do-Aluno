import secrets

from django.conf import settings
from django.core.exceptions import ValidationError

_SIGNATURES = (
    ("pdf", b"%PDF-"),
    ("png", b"\x89PNG\r\n\x1a\n"),
    ("jpg", b"\xff\xd8\xff"),
)


def detect_kind(uploaded) -> str | None:
    head = uploaded.read(16)
    uploaded.seek(0)
    for kind, signature in _SIGNATURES:
        if head.startswith(signature):
            return kind
    return None


def check_upload(uploaded, allowed=("pdf",)) -> str:
    """Valida tamanho e tipo real (pelo conteúdo). Retorna o tipo detectado."""
    if uploaded.size > settings.MAX_UPLOAD_BYTES:
        limite = settings.MAX_UPLOAD_BYTES // (1024 * 1024)
        raise ValidationError(f"O arquivo excede o tamanho máximo de {limite} MB.")
    kind = detect_kind(uploaded)
    if kind not in allowed:
        aceitos = ", ".join(a.upper() for a in allowed)
        raise ValidationError(f"Tipo de arquivo não permitido. Formatos aceitos: {aceitos}.")
    return kind


def prepare_upload(uploaded, allowed=("pdf",)) -> str:
    """Valida o arquivo e troca o nome por um aleatório.

    O nome original do cliente é descartado, evitando path traversal e
    URLs previsíveis.
    """
    kind = check_upload(uploaded, allowed)
    uploaded.name = f"{secrets.token_hex(16)}.{kind}"
    return kind
