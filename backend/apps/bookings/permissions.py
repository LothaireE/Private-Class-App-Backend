from rest_framework import permissions


def is_coach_owner(user, coach_profile):
    return bool(user and user.is_authenticated and coach_profile.user_id == user.id)


def is_student_owner(user, student_profile):
    return bool(user and user.is_authenticated and student_profile.user_id == user.id)


class IsBookingParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return is_coach_owner(request.user, obj.coach) or is_student_owner(request.user, obj.student)


class IsSessionParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return is_coach_owner(request.user, obj.coach) or is_student_owner(request.user, obj.student)
