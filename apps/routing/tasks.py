from celery import shared_task

from apps.core.enums import RequestStatus


@shared_task
def check_escalation_timeout(request_id, escalation_level):
    from apps.requests_app.models import SacramentRequest

    try:
        sacrament_request = SacramentRequest.objects.get(id=request_id)
    except SacramentRequest.DoesNotExist:
        return

    if sacrament_request.status != RequestStatus.ROUTED:
        return  # already accepted/cancelled/completed - no-op

    latest = sacrament_request.escalations.order_by("-escalation_level").first()
    if not latest or latest.escalation_level != escalation_level or latest.resolved_at is not None:
        return  # a newer escalation (or acceptance) already superseded this one

    from .services import escalate_request

    escalate_request(sacrament_request, reason="no_response_timeout")
