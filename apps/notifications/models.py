from django.conf import settings
from django.db import models

from apps.core.enums import NotificationChannel, NotificationStatus, NotificationType
from apps.core.models import TimeStampedModel


class NotificationLog(TimeStampedModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="notifications",
        null=True,
        blank=True,
    )
    recipient_phone = models.CharField(max_length=20, blank=True)
    channel = models.CharField(max_length=10, choices=NotificationChannel.choices)
    notification_type = models.CharField(max_length=40, choices=NotificationType.choices)
    related_request = models.ForeignKey(
        "requests_app.SacramentRequest",
        on_delete=models.SET_NULL,
        related_name="notification_logs",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=10, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    provider_message_id = models.CharField(max_length=100, blank=True)
    payload_summary = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.channel}:{self.notification_type} -> {self.recipient or self.recipient_phone} ({self.status})"
