import random
import string

from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.enums import RequestStatus

from .models import RequestStatusEvent, SacramentRequest

# Coarse lifecycle stages only; escalation depth is tracked via RequestEscalation
# rows in the routing app, not as a separate top-level status here.
ALLOWED_STATUS_TRANSITIONS = {
    RequestStatus.SUBMITTED: {RequestStatus.ROUTED, RequestStatus.CANCELLED, RequestStatus.EXPIRED},
    RequestStatus.ROUTED: {RequestStatus.ACCEPTED, RequestStatus.CANCELLED, RequestStatus.EXPIRED},
    RequestStatus.ACCEPTED: {RequestStatus.EN_ROUTE, RequestStatus.CANCELLED},
    RequestStatus.EN_ROUTE: {RequestStatus.COMPLETED, RequestStatus.CANCELLED},
}


def _generate_tracking_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(20):
        code = "SAC-" + "".join(random.choices(alphabet, k=5))
        if not SacramentRequest.objects.filter(tracking_code=code).exists():
            return code
    raise RuntimeError("Could not generate a unique tracking code.")


@transaction.atomic
def create_sacrament_request(*, data: dict, channel: str, requester=None) -> SacramentRequest:
    """
    The single place a SacramentRequest is created from. Both the DRF
    serializer (web/mobile) and the USSD webhook view call this so
    request-creation business logic never has two implementations.
    """
    location = None
    lat, lng = data.pop("latitude", None), data.pop("longitude", None)
    if lat is not None and lng is not None:
        location = Point(float(lng), float(lat), srid=4326)

    sacrament_request = SacramentRequest.objects.create(
        tracking_code=_generate_tracking_code(),
        requester=requester,
        channel=channel,
        location=location,
        **data,
    )
    RequestStatusEvent.objects.create(
        request=sacrament_request, from_status="", to_status=RequestStatus.SUBMITTED
    )

    from apps.notifications.services import notify

    notify(
        user=requester,
        phone=sacrament_request.requester_phone,
        notification_type="request_submitted_ack",
        context={"tracking_code": sacrament_request.tracking_code},
        channels=["sms"],
    )

    from apps.routing.services import route_request

    route_request(sacrament_request)

    return sacrament_request


def _transition_status(*, sacrament_request: SacramentRequest, to_status: str, actor=None, notes: str = ""):
    from_status = sacrament_request.status
    if to_status not in ALLOWED_STATUS_TRANSITIONS.get(from_status, set()):
        raise ValidationError(f"Cannot transition request from {from_status} to {to_status}.")

    sacrament_request.status = to_status
    if to_status == RequestStatus.ACCEPTED:
        sacrament_request.responded_at = timezone.now()
    if to_status == RequestStatus.COMPLETED:
        sacrament_request.completed_at = timezone.now()
    sacrament_request.save()

    RequestStatusEvent.objects.create(
        request=sacrament_request,
        from_status=from_status,
        to_status=to_status,
        changed_by=actor,
        notes=notes,
    )
    return sacrament_request


def accept_request(*, sacrament_request: SacramentRequest, priest_profile) -> SacramentRequest:
    if sacrament_request.status not in (RequestStatus.ROUTED, RequestStatus.SUBMITTED):
        raise ValidationError("This request is no longer available to accept.")

    from apps.routing.services import cancel_pending_escalation

    sacrament_request.assigned_priest = priest_profile
    _transition_status(
        sacrament_request=sacrament_request, to_status=RequestStatus.ACCEPTED, actor=priest_profile.user
    )
    cancel_pending_escalation(sacrament_request)

    from apps.notifications.services import notify

    notify(
        user=sacrament_request.requester,
        phone=sacrament_request.requester_phone,
        notification_type="request_accepted_confirmation",
        context={"priest_name": priest_profile.user.get_full_name(), "tracking_code": sacrament_request.tracking_code},
        channels=["sms"],
    )
    return sacrament_request


def decline_request(*, sacrament_request: SacramentRequest, priest_profile) -> SacramentRequest:
    if sacrament_request.assigned_priest_id and sacrament_request.assigned_priest_id != priest_profile.id:
        raise PermissionDenied("You are not the priest currently assigned to this request.")

    from apps.routing.services import escalate_request

    escalate_request(sacrament_request, reason="priest_declined")
    return sacrament_request


def update_request_status(*, sacrament_request: SacramentRequest, to_status: str, actor) -> SacramentRequest:
    return _transition_status(sacrament_request=sacrament_request, to_status=to_status, actor=actor)


def cancel_request(*, sacrament_request: SacramentRequest, actor) -> SacramentRequest:
    from apps.routing.services import cancel_pending_escalation

    result = _transition_status(
        sacrament_request=sacrament_request, to_status=RequestStatus.CANCELLED, actor=actor
    )
    cancel_pending_escalation(sacrament_request)
    return result
