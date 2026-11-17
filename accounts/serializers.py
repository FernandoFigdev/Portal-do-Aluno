from rest_framework import serializers

from .models import StudentProfile, User


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ["registration_number", "course"]


class MeSerializer(serializers.ModelSerializer):
    student = StudentProfileSerializer(source="student_profile", read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "role", "student"]
        read_only_fields = fields