from django.db import models


class IntegrationLog(models.Model):
    """Resultado de operações contra sistemas externos (ERS 8.8)."""

    system = models.CharField(max_length=40)
    operation = models.CharField(max_length=40)
    success = models.BooleanField()
    message = models.CharField(max_length=255, blank=True)  # mensagem técnica segura
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.system}/{self.operation}: {'ok' if self.success else 'falha'}"
