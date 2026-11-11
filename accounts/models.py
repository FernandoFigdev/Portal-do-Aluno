from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Aluno"
        STAFF = "STAFF", "Secretaria"
        ADMIN = "ADMIN", "Administrador"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)

    @property
    def is_secretary(self) -> bool:
        return self.role in (self.Role.STAFF, self.Role.ADMIN)

    def save(self, *args, **kwargs):
        # Superusuário criado via createsuperuser sempre nasce como administrador
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    registration_number = models.CharField("Matrícula", max_length=30, unique=True)
    course = models.CharField("Curso", max_length=120, blank=True)
    external_ids = models.JSONField(
        default=dict,
        blank=True,
        help_text='IDs do aluno nos sistemas externos. Ex.: {"moodle": 123, "cerbrum": "A-998"}',
    )

    def __str__(self):
        return f"{self.registration_number} - {self.user.get_full_name() or self.user.username}"