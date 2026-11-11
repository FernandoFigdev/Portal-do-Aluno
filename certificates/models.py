from django.conf import settings
from django.db import models

from core.storage import private_storage


def certificate_upload_path(instance, filename):
    # `filename` já é aleatório (core.validators.prepare_upload)
    return f"certificates/{instance.student_id}/{filename}"


class Certificate(models.Model):
    student = models.ForeignKey(
        "accounts.StudentProfile", on_delete=models.PROTECT, related_name="certificates"
    )
    category = models.CharField(
        "Categoria", max_length=80,
        help_text="Ex.: Atividade complementar, Evento, Monitoria (categorias a confirmar com a instituição).",
    )
    title = models.CharField("Identificação", max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=certificate_upload_path, storage=private_storage)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.title} ({self.student.registration_number})"
