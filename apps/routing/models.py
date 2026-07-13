from django.conf import settings
from django.db import models

from apps.core.enums import EscalationReason
from apps.core.models import TimeStampedModel


class RequestEscalation(TimeStampedModel):
    request = models.ForeignKey(
        "requests_app.SacramentRequest", on_delete=models.CASCADE, related_name="escalations"
    )
    escalation_level = models.PositiveIntegerField(default=0)
    escalated_to_priest = models.ForeignKey(
        "clergy.PriestProfile",
        on_delete=models.SET_NULL,
        related_name="escalations_received",
        null=True,
        blank=True,
    )
    escalated_to_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="escalations_received",
        null=True,
        blank=True,
    )
    escalated_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=30, choices=EscalationReason.choices)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-escalated_at"]

    def __str__(self):
        return f"{self.request.tracking_code} L{self.escalation_level} ({self.reason})"
