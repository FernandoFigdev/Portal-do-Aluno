from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.reverse import reverse

from core.validators import prepare_upload

from .models import DocumentRequest, DocumentType, StatusHistory


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ["id", "name", "description", "required_fields"]


class AdminDocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ["id", "name", "description", "required_fields", "active"]

    def validate_required_fields(self, value):
        if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
            raise serializers.ValidationError("Informe uma lista de nomes de campos (texto).")
        return [v.strip() for v in value]


class StatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusHistory
        fields = ["from_status", "to_status", "note", "created_at"]


class AdminStatusHistorySerializer(StatusHistorySerializer):
    changed_by = serializers.SerializerMethodField()

    class Meta(StatusHistorySerializer.Meta):
        fields = StatusHistorySerializer.Meta.fields + ["changed_by"]

    def get_changed_by(self, obj):
        return obj.changed_by.username if obj.changed_by else None


class DocumentRequestCreateSerializer(serializers.Serializer):
    document_type = serializers.PrimaryKeyRelatedField(
        queryset=DocumentType.objects.filter(active=True)
    )
    data = serializers.JSONField(required=False, default=dict)


class DocumentRequestSerializer(serializers.ModelSerializer):
    document_type = DocumentTypeSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    history = StatusHistorySerializer(many=True, read_only=True)
    has_file = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = DocumentRequest
        fields = [
            "protocol", "document_type", "data", "status", "status_display",
            "created_at", "updated_at", "has_file", "download_url", "history",
        ]
        read_only_fields = fields

    download_route = "my-requests-download"

    def get_has_file(self, obj):
        return hasattr(obj, "final_file")

    def get_download_url(self, obj):
        if not hasattr(obj, "final_file"):
            return None
        return reverse(self.download_route, args=[obj.protocol], request=self.context.get("request"))


class AdminDocumentRequestSerializer(DocumentRequestSerializer):
    history = AdminStatusHistorySerializer(many=True, read_only=True)
    student = serializers.SerializerMethodField()
    allowed_transitions = serializers.SerializerMethodField()

    download_route = "admin-requests-arquivo"

    class Meta(DocumentRequestSerializer.Meta):
        fields = DocumentRequestSerializer.Meta.fields + ["student", "allowed_transitions"]
        read_only_fields = fields

    def get_student(self, obj):
        return {
            "registration_number": obj.student.registration_number,
            "name": obj.student.user.get_full_name() or obj.student.user.username,
            "course": obj.student.course,
        }

    def get_allowed_transitions(self, obj):
        return obj.allowed_transitions()


class StatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=DocumentRequest.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255, default="")


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
