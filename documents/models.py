import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.storage import private_storage


class DocumentType(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    required_fields = models.JSONField(
        default=list, blank=True,
        help_text='Campos que o aluno deve preencher. Ex.: ["finalidade"]',
    )
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DocumentRequest(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Recebida"
        IN_REVIEW = "IN_REVIEW", "Em análise"
        AWAITING_INFO = "AWAITING_INFO", "Aguardando informação"
        COMPLETED = "COMPLETED", "Concluída"
        REJECTED = "REJECTED", "Indeferida"

    # Transições permitidas (lista a validar com a secretaria, ERS RF16)
    TRANSITIONS = {
        Status.RECEIVED: {Status.IN_REVIEW, Status.REJECTED},
        Status.IN_REVIEW: {Status.AWAITING_INFO, Status.COMPLETED, Status.REJECTED},
        Status.AWAITING_INFO: {Status.IN_REVIEW, Status.REJECTED},
        Status.COMPLETED: set(),
        Status.REJECTED: set(),
    }

    protocol = models.CharField(max_length=20, unique=True, editable=False)
    student = models.ForeignKey(
        "accounts.StudentProfile", on_delete=models.PROTECT, related_name="document_requests"
    )
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT)
    data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.protocol

    def allowed_transitions(self) -> list[str]:
        return sorted(s.value for s in self.TRANSITIONS[self.Status(self.status)])

    def can_transition_to(self, new_status) -> bool:
        return new_status in self.allowed_transitions()

    @classmethod
    def generate_protocol(cls) -> str:
        year = timezone.now().year
        while True:
            candidate = f"{year}-{secrets.token_hex(4).upper()}"
            if not cls.objects.filter(protocol=candidate).exists():
                return candidate

    def save(self, *args, **kwargs):
        if not self.protocol:
            self.protocol = self.generate_protocol()
        super().save(*args, **kwargs)


class StatusHistory(models.Model):
    request = models.ForeignKey(DocumentRequest, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


def document_upload_path(instance, filename):
    # `filename` já é aleatório (core.validators.prepare_upload)
    return f"documents/{instance.request.protocol}/{filename}"


class DocumentFile(models.Model):
    request = models.OneToOneField(DocumentRequest, on_delete=models.CASCADE, related_name="final_file")
    file = models.FileField(upload_to=document_upload_path, storage=private_storage)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    uploaded_at = models.DateTimeField(auto_now=True)
