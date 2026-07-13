from rest_framework.permissions import BasePermission

from apps.core.enums import UserRole, VerificationStatus


class IsMember(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.MEMBER)


class IsVerifiedPriest(BasePermission):
    """
    The single gate for all priest-only functionality.

    Being role=priest is never sufficient on its own - every priest-only view
    must also confirm the attached PriestProfile has cleared diocesan
    verification. Centralizing both checks here means no view can forget the
    verification half.
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.role == UserRole.PRIEST):
            return False
        profile = getattr(user, "priest_profile", None)
        return bool(profile and profile.verification_status == VerificationStatus.VERIFIED)


class IsDiocesanAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.DIOCESAN_ADMIN
        )


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.SUPER_ADMIN
        )


class IsDiocesanAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (UserRole.DIOCESAN_ADMIN, UserRole.SUPER_ADMIN)
        )


class IsSameDioceseAdminOrSuperAdmin(BasePermission):
    """Object-level check: diocesan admins may only act on objects within their own diocese."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == UserRole.SUPER_ADMIN:
            return True
        if user.role != UserRole.DIOCESAN_ADMIN:
            return False
        admin_profile = getattr(user, "diocesan_admin_profile", None)
        obj_diocese = getattr(obj, "diocese", None)
        return bool(admin_profile and obj_diocese and admin_profile.diocese_id == obj_diocese.id)
