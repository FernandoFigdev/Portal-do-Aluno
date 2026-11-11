from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "student", "created_at")
    list_filter = ("category",)
    search_fields = ("title", "student__registration_number")
