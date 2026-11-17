from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import StudentProfile, User


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    extra = 0


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Perfil no portal", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Perfil no portal", {"fields": ("role",)}),)
    list_display = ("username", "first_name", "last_name", "role", "is_active")
    list_filter = UserAdmin.list_filter + ("role",)
    inlines = [StudentProfileInline]