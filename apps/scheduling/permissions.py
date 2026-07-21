from rest_framework import permissions


class IsSlotCoachOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.coach.user_id == request.user.id
