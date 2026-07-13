from django.db import transaction

from .models import NotificationLog
from .templates import render_message


def notify(*, user=None, phone: str = "", notification_type: str, context: dict, channels: list[str]):
    """
    Single dispatcher for all outbound comms. Always writes a NotificationLog
    row per channel attempted (auditable regardless of delivery outcome), and
    hands actual sending off to a Celery task so a slow SMS/email gateway
    never blocks the calling request/response cycle.

    Callers (e.g. create_sacrament_request) often run inside
    @transaction.atomic. Dispatching .delay() immediately would let the
    Celery worker query for the NotificationLog row before the transaction
    commits, silently no-op'ing on a DoesNotExist race. transaction.on_commit
    defers the dispatch until the surrounding transaction (if any) actually
    commits; outside a transaction it runs immediately.
    """
    from .tasks import send_notification

    message = render_message(notification_type, context)
    recipient_phone = phone or getattr(user, "phone_number", "")
    recipient_email = getattr(user, "email", "")

    logs = []
    for channel in channels:
        if channel == "email" and not recipient_email:
            continue
        if channel in ("sms", "push") and not recipient_phone:
            continue
        log = NotificationLog.objects.create(
            recipient=user if user and user.is_authenticated else None,
            recipient_phone=recipient_phone,
            channel=channel,
            notification_type=notification_type,
            related_request=context.get("_related_request"),
            payload_summary=message[:255],
        )
        logs.append(log)
        transaction.on_commit(
            lambda log_id=log.id: send_notification.delay(log_id, message, recipient_phone, recipient_email)
        )
    return logs
