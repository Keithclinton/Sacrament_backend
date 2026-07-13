from rest_framework.permissions import BasePermission

from apps.core.enums import UserRole


class IsOwnerAssignedPriestOrScopedAdmin(BasePermission):
    """Object-level: the requester, the assigned priest, or an admin scoped to the relevant diocese."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if obj.requester_id == user.id:
            return True
        priest_profile = getattr(user, "priest_profile", None)
        if priest_profile and obj.assigned_priest_id == priest_profile.id:
            return True
        if user.role == UserRole.SUPER_ADMIN:
            return True
        if user.role == UserRole.DIOCESAN_ADMIN:
            admin_profile = getattr(user, "diocesan_admin_profile", None)
            request_diocese_id = obj.assigned_parish.diocese_id if obj.assigned_parish else None
            return bool(admin_profile and request_diocese_id and admin_profile.diocese_id == request_diocese_id)
        return False
