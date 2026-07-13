from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import Count, ExpressionWrapper, F, FloatField, Q
from django.utils import timezone

from apps.clergy.models import PriestProfile
from apps.core.enums import EscalationReason, RequestStatus, VerificationStatus

from .models import RequestEscalation

ACTIVE_REQUEST_STATUSES = (RequestStatus.ROUTED, RequestStatus.ACCEPTED, RequestStatus.EN_ROUTE)


def find_nearest_available_priests(location, exclude_ids=None, limit=5):
    """
    Progressively widen the search radius (see ROUTING_RADIUS_TIERS_KM) so
    rural requests with few nearby priests still get a match before falling
    back to diocesan-admin dispatch.

    Ranking is workload-aware: raw distance is combined with a penalty per
    currently active assigned request, so a nearby but already-overloaded
    priest doesn't always get piled on ahead of a slightly farther idle one.
    """
    exclude_ids = exclude_ids or []
    for radius_km in settings.ROUTING_RADIUS_TIERS_KM:
        candidates = list(
            PriestProfile.objects.filter(
                verification_status=VerificationStatus.VERIFIED,
                is_available=True,
                current_location__isnull=False,
            )
            .exclude(id__in=exclude_ids)
            .filter(current_location__distance_lte=(location, D(km=radius_km)))
            .annotate(
                distance=Distance("current_location", location),
                active_request_count=Count(
                    "assigned_requests",
                    filter=Q(assigned_requests__status__in=ACTIVE_REQUEST_STATUSES),
                    distinct=True,
                ),
            )
            .annotate(
                workload_score=ExpressionWrapper(
                    F("distance")
                    + F("active_request_count") * settings.WORKLOAD_PENALTY_METERS_PER_ACTIVE_REQUEST,
                    output_field=FloatField(),
                )
            )
            .order_by("workload_score")[:limit]
        )
        if candidates:
            return candidates
    return []


def _schedule_timeout_task(sacrament_request, escalation_level):
    from .tasks import check_escalation_timeout

    timeout_minutes = settings.ESCALATION_TIMEOUT_MINUTES.get(sacrament_request.emergency_level, 60)
    check_escalation_timeout.apply_async(
        args=[str(sacrament_request.id), escalation_level], countdown=timeout_minutes * 60
    )


def _notify_diocesan_admin_fallback(sacrament_request):
    from apps.accounts.models import DiocesanAdminProfile
    from apps.core.enums import UserRole
    from apps.notifications.services import notify

    diocese = sacrament_request.assigned_parish.diocese if sacrament_request.assigned_parish else None
    if diocese:
        recipients = [ap.user for ap in DiocesanAdminProfile.objects.filter(diocese=diocese)]
    else:
        from apps.accounts.models import User

        recipients = list(User.objects.filter(role=UserRole.SUPER_ADMIN))

    for user in recipients:
        notify(
            user=user,
            notification_type="escalation_alert",
            context={"tracking_code": sacrament_request.tracking_code, "reason": "no_priest_available"},
            channels=["sms", "email"],
        )


def route_request(sacrament_request):
    """Called once at creation time to find & notify the first candidate priest."""
    if not sacrament_request.location:
        from .geocoding import resolve_location_from_description

        resolved = resolve_location_from_description(sacrament_request.location_description)
        if resolved:
            sacrament_request.location = resolved
            sacrament_request.save(update_fields=["location", "updated_at"])
        else:
            # No GPS and no recognizable landmark: leave unrouted for manual diocesan dispatch.
            _notify_diocesan_admin_fallback(sacrament_request)
            return

    candidates = find_nearest_available_priests(sacrament_request.location)
    if not candidates:
        _notify_diocesan_admin_fallback(sacrament_request)
        return

    top_candidate = candidates[0]
    sacrament_request.assigned_parish = top_candidate.parish
    sacrament_request.status = RequestStatus.ROUTED
    sacrament_request.save(update_fields=["assigned_parish", "status", "updated_at"])

    RequestEscalation.objects.create(
        request=sacrament_request,
        escalation_level=0,
        escalated_to_priest=top_candidate,
        reason=EscalationReason.INITIAL_ROUTING,
    )

    from apps.notifications.services import notify

    notify(
        user=top_candidate.user,
        notification_type="priest_new_request_alert",
        context={"tracking_code": sacrament_request.tracking_code, "emergency_level": sacrament_request.emergency_level},
        channels=["sms", "push"],
    )

    _schedule_timeout_task(sacrament_request, escalation_level=0)


def escalate_request(sacrament_request, reason):
    latest = sacrament_request.escalations.order_by("-escalation_level").first()
    current_level = latest.escalation_level if latest else 0

    if latest and latest.resolved_at is None:
        latest.resolved_at = timezone.now()
        latest.save(update_fields=["resolved_at"])

    next_level = current_level + 1
    if next_level > settings.MAX_ESCALATION_LEVELS:
        _notify_diocesan_admin_fallback(sacrament_request)
        return

    exclude_ids = list(
        sacrament_request.escalations.exclude(escalated_to_priest__isnull=True).values_list(
            "escalated_to_priest_id", flat=True
        )
    )
    candidates = (
        find_nearest_available_priests(sacrament_request.location, exclude_ids=exclude_ids)
        if sacrament_request.location
        else []
    )
    if not candidates:
        _notify_diocesan_admin_fallback(sacrament_request)
        return

    next_candidate = candidates[0]
    RequestEscalation.objects.create(
        request=sacrament_request,
        escalation_level=next_level,
        escalated_to_priest=next_candidate,
        reason=reason,
    )

    from apps.notifications.services import notify

    notify(
        user=next_candidate.user,
        notification_type="priest_new_request_alert",
        context={"tracking_code": sacrament_request.tracking_code, "emergency_level": sacrament_request.emergency_level},
        channels=["sms", "push"],
    )

    _schedule_timeout_task(sacrament_request, escalation_level=next_level)


def cancel_pending_escalation(sacrament_request):
    latest = sacrament_request.escalations.filter(resolved_at__isnull=True).order_by("-escalation_level").first()
    if latest:
        latest.resolved_at = timezone.now()
        latest.save(update_fields=["resolved_at"])


def get_pending_request_ids_for_priest(priest_profile):
    """
    Requests currently offered to this priest awaiting accept/decline -
    distinct from `assigned_priest`, which is only set once they accept.
    Used to build a priest's "awaiting my response" queue.
    """
    return RequestEscalation.objects.filter(
        escalated_to_priest=priest_profile, resolved_at__isnull=True
    ).values_list("request_id", flat=True)
