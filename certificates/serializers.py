from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.reverse import reverse

from accounts.models import StudentProfile
from core.validators import check_upload

from . import services
from .models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    """Visão do aluno (RF21, RF23)."""

    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = ["id", "category", "title", "description", "created_at", "download_url"]
        read_only_fields = fields

    def get_download_url(self, obj):
        return reverse("my-certificates-download", args=[obj.pk], request=self.context.get("request"))


class AdminCertificateSerializer(serializers.ModelSerializer):
    """Visão da secretaria (RF22, RF24). O aluno é informado pela matrícula."""

    student = serializers.SlugRelatedField(
        slug_field="registration_number", queryset=StudentProfile.objects.select_related("user"),
    )
    student_name = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True, required=False)
    uploaded_by = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = [
            "id", "student", "student_name", "category", "title", "description",
            "file", "uploaded_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_student_name(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.username

    def get_uploaded_by(self, obj):
        return obj.uploaded_by.username if obj.uploaded_by else None

    def validate_file(self, uploaded):
        try:
            check_upload(uploaded, allowed=services.ALLOWED_KINDS)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return uploaded

    def validate(self, attrs):
        if self.instance is None and "file" not in attrs:
            raise serializers.ValidationError({"file": "Este campo é obrigatório."})
        return attrs

    def create(self, validated_data):
        return services.create_certificate(self.context["request"].user, **validated_data)

    def update(self, instance, validated_data):
        return services.update_certificate(instance, self.context["request"].user, **validated_data)
