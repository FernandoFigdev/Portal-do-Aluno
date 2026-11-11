from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from integrations.base import IntegrationError


def api_exception_handler(exc, context):
    # Erros de regra de negócio levantados pelos services -> HTTP 400
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = DRFValidationError(exc.message_dict)
        else:
            exc = DRFValidationError(exc.messages)

    # Falhas de integração externa -> mensagem clara, sem derrubar a API (RF11, RNF08, RN09)
    if isinstance(exc, IntegrationError):
        return Response(
            {"code": exc.code, "detail": str(exc)},
            status=exc.http_status,
        )

    return exception_handler(exc, context)
