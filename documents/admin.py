from django.contrib import admin

from .models import DocumentFile, DocumentRequest, DocumentType, StatusHistory


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "active")


class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "note", "created_at")
    can_delete = False


@admin.register(DocumentRequest)
class DocumentRequestAdmin(admin.ModelAdmin):
    list_display = ("protocol", "student", "document_type", "status", "created_at")
    list_filter = ("status", "document_type")
    search_fields = ("protocol", "student__registration_number")
    inlines = [StatusHistoryInline]
    # Alterações de estado devem passar pela API/serviços para gerar histórico e auditoria
    readonly_fields = ("protocol", "student", "document_type", "data", "status")


admin.site.register(DocumentFile)
