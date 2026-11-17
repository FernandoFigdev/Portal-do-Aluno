from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Registro de operações administrativas (RF25, RNF10)."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    action = models.CharField(max_length=60, db_index=True)
    target_type = models.CharField(max_length=60)
    target_id = models.CharField(max_length=60)
    details = models.JSONField(default=dict, blank=True)  # nunca contém segredos
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.action} {self.target_type}#{self.target_id}"
