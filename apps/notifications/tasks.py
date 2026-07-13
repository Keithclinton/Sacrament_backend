from celery import shared_task
from django.utils import timezone

from apps.core.enums import NotificationStatus

from .channels import CHANNEL_REGISTRY


@shared_task
def send_notification(log_id, message, phone, email):
    from .models import NotificationLog

    try:
        log = NotificationLog.objects.get(id=log_id)
    except NotificationLog.DoesNotExist:
        return

    channel = CHANNEL_REGISTRY.get(log.channel)
    if channel is None:
        log.status = NotificationStatus.FAILED
        log.error_message = f"Unknown channel: {log.channel}"
        log.save(update_fields=["status", "error_message", "updated_at"])
        return

    success, provider_message_id, error_message = channel.send(phone=phone, email=email, message=message)
    log.status = NotificationStatus.SENT if success else NotificationStatus.FAILED
    log.provider_message_id = provider_message_id
    log.error_message = error_message
    log.sent_at = timezone.now() if success else None
    log.save(update_fields=["status", "provider_message_id", "error_message", "sent_at", "updated_at"])
