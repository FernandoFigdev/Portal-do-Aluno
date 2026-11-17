from django.core.exceptions import ValidationError
from django.db import transaction

from core.audit import audit
from core.validators import prepare_upload

from .models import DocumentFile, DocumentRequest, StatusHistory


@transaction.atomic
def create_request(student_profile, document_type, data: dict) -> DocumentRequest:
    """RF14/RF15: valida campos obrigatórios, gera protocolo e abre o histórico."""
    if not document_type.active:
        raise ValidationError({"document_type": "Este tipo de documento não está disponível."})
    if not isinstance(data, dict):
        raise ValidationError({"data": "Formato inválido."})

    clean = {k: (v.strip() if isinstance(v, str) else v) for k, v in data.items()}
    missing = [f for f in document_type.required_fields if clean.get(f) in (None, "", [])]
    if missing:
        raise ValidationError({"data": f"Campos obrigatórios ausentes: {', '.join(missing)}."})

    request = DocumentRequest.objects.create(
        student=student_profile, document_type=document_type, data=clean
    )
    StatusHistory.objects.create(
        request=request, to_status=request.status,
        changed_by=student_profile.user, note="Solicitação registrada.",
    )
    return request


@transaction.atomic
def change_status(request: DocumentRequest, new_status: str, actor, note: str = "") -> DocumentRequest:
    """RF16/RF17: aplica somente transições permitidas e registra histórico + auditoria."""
    request = DocumentRequest.objects.select_for_update().get(pk=request.pk)

    if new_status not in DocumentRequest.Status.values:
        raise ValidationError({"status": "Estado inválido."})
    if not request.can_transition_to(new_status):
        raise ValidationError(
            {"status": f"Transição não permitida: {request.status} → {new_status}."}
        )
    if (
        new_status == DocumentRequest.Status.COMPLETED
        and not DocumentFile.objects.filter(request=request).exists()
    ):
        raise ValidationError(
            {"status": "Anexe o documento final em PDF antes de concluir a solicitação."}
        )

    old = request.status
    request.status = new_status
    request.save(update_fields=["status", "updated_at"])
    StatusHistory.objects.create(
        request=request, from_status=old, to_status=new_status, changed_by=actor, note=note[:255],
    )
    audit(actor, "REQUEST_STATUS_CHANGED", request, {"from": old, "to": new_status})
    return request


@transaction.atomic
def attach_final_file(request: DocumentRequest, uploaded, actor) -> DocumentFile:
    """RF18/RF20: valida o PDF e o vincula à solicitação correta (RN07)."""
    if request.status == DocumentRequest.Status.REJECTED:
        raise ValidationError("Não é possível anexar documento a uma solicitação indeferida.")

    prepare_upload(uploaded, allowed=("pdf",))

    existing = DocumentFile.objects.filter(request=request).first()
    old_name = existing.file.name if existing else None

    document, _ = DocumentFile.objects.update_or_create(
        request=request, defaults={"file": uploaded, "uploaded_by": actor}
    )
    if old_name and old_name != document.file.name:
        transaction.on_commit(lambda: document.file.storage.delete(old_name))

    audit(actor, "REQUEST_FILE_ATTACHED", request, {"replaced": bool(old_name)})
    return document
