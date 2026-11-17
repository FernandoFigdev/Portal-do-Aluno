from django.contrib import admin

from .models import IntegrationLog


@admin.register(IntegrationLog)
class IntegrationLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "system", "operation", "success", "message")
    list_filter = ("system", "success")
