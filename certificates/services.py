from django.db import transaction

from core.audit import audit
from core.validators import prepare_upload

from .models import Certificate

ALLOWED_KINDS = ("pdf", "png", "jpg")


@transaction.atomic
def create_certificate(actor, *, student, category, title, file, description="") -> Certificate:
    """RF22/RN08: cadastra o certificado já associado ao aluno correto."""
    prepare_upload(file, allowed=ALLOWED_KINDS)
    certificate = Certificate.objects.create(
        student=student, category=category, title=title,
        description=description, file=file, uploaded_by=actor,
    )
    audit(actor, "CERTIFICATE_CREATED", certificate, {
        "student": student.registration_number, "category": category,
    })
    return certificate


@transaction.atomic
def update_certificate(certificate: Certificate, actor, **fields) -> Certificate:
    """RF24: correção de registros (metadados, aluno associado ou arquivo)."""
    changed = []
    old_name = None

    new_file = fields.pop("file", None)
    if new_file is not None:
        prepare_upload(new_file, allowed=ALLOWED_KINDS)
        old_name = certificate.file.name
        certificate.file = new_file
        changed.append("file")

    previous_student = certificate.student.registration_number
    for name, value in fields.items():
        if getattr(certificate, name) != value:
            setattr(certificate, name, value)
            changed.append(name)

    certificate.uploaded_by = certificate.uploaded_by or actor
    certificate.save()

    if old_name and old_name != certificate.file.name:
        transaction.on_commit(lambda: certificate.file.storage.delete(old_name))

    details = {"fields": changed}
    if "student" in changed:
        details["student_from"] = previous_student
        details["student_to"] = certificate.student.registration_number
    audit(actor, "CERTIFICATE_UPDATED", certificate, details)
    return certificate
