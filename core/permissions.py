from rest_framework.permissions import BasePermission


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user.is_authenticated
            and user.role == "STUDENT"
            and hasattr(user, "student_profile")
        )


class IsSecretary(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.is_secretary)


class IsAdministrator(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and user.role == "ADMIN")
