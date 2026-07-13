from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.core.enums import UserRole, VerificationStatus

from .models import PriestProfile, PriestVerificationEvent

# Explicit allowed transitions: from_status -> set of to_statuses.
ALLOWED_TRANSITIONS = {
    VerificationStatus.PENDING: {VerificationStatus.UNDER_REVIEW},
    VerificationStatus.UNDER_REVIEW: {VerificationStatus.VERIFIED, VerificationStatus.REJECTED},
    VerificationStatus.VERIFIED: {VerificationStatus.SUSPENDED},
    VerificationStatus.REJECTED: {VerificationStatus.PENDING},
    VerificationStatus.SUSPENDED: {VerificationStatus.VERIFIED},
}


def _actor_can_manage_diocese(actor, priest_profile) -> bool:
    if actor.role == UserRole.SUPER_ADMIN:
        return True
    if actor.role != UserRole.DIOCESAN_ADMIN:
        return False
    admin_profile = getattr(actor, "diocesan_admin_profile", None)
    return bool(admin_profile and admin_profile.diocese_id == priest_profile.diocese_id)


def transition_priest_verification(
    *, priest_profile: PriestProfile, to_status: str, actor, notes: str = ""
) -> PriestProfile:
    from_status = priest_profile.verification_status

    if to_status not in ALLOWED_TRANSITIONS.get(from_status, set()):
        raise ValidationError(f"Cannot transition priest from {from_status} to {to_status}.")

    # Reinstating from suspended is a higher-trust action reserved for super admins.
    if from_status == VerificationStatus.SUSPENDED and to_status == VerificationStatus.VERIFIED:
        if actor.role != UserRole.SUPER_ADMIN:
            raise PermissionDenied("Only a super admin can reinstate a suspended priest.")
    elif not _actor_can_manage_diocese(actor, priest_profile):
        raise PermissionDenied("You may only manage priests within your own diocese.")

    if to_status == VerificationStatus.REJECTED and not notes:
        raise ValidationError("Rejection requires explanatory notes.")

    priest_profile.verification_status = to_status
    if to_status == VerificationStatus.VERIFIED:
        priest_profile.verified_by = actor
        priest_profile.verified_at = timezone.now()
    if notes:
        priest_profile.verification_notes = notes
    priest_profile.save(
        update_fields=["verification_status", "verified_by", "verified_at", "verification_notes", "updated_at"]
    )

    PriestVerificationEvent.objects.create(
        priest_profile=priest_profile,
        from_status=from_status,
        to_status=to_status,
        changed_by=actor,
        notes=notes,
    )

    from apps.notifications.services import notify

    notify(
        user=priest_profile.user,
        notification_type="verification_decision",
        context={"to_status": to_status, "notes": notes},
        channels=["sms", "email"],
    )

    return priest_profile
