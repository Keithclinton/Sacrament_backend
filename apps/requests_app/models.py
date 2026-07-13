from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models

from apps.core.enums import (
    EmergencyLevel,
    HospitalOrHome,
    RequestChannel,
    RequestStatus,
    SacramentType,
)
from apps.core.models import TimeStampedModel, UUIDModel


class SacramentRequest(UUIDModel, TimeStampedModel):
    """
    The core domain object. This is strictly a logistics/coordination record:
    it MUST NEVER contain a field for confession content, sins, or any
    sacramental conversation. Only metadata, location, urgency, and contact
    details are captured here - by design, not by convention.
    """

    tracking_code = models.CharField(max_length=12, unique=True, db_index=True)

    # Nullable: USSD/anonymous requesters may have no account at all.
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="sacrament_requests",
        null=True,
        blank=True,
    )
    requester_name = models.CharField(max_length=200)
    requester_phone = models.CharField(max_length=20)

    patient_name = models.CharField(max_length=200)
    sacrament_type = models.CharField(max_length=30, choices=SacramentType.choices)
    emergency_level = models.CharField(max_length=30, choices=EmergencyLevel.choices)

    location = gis_models.PointField(geography=True, null=True, blank=True)
    location_description = models.TextField(
        blank=True, help_text="Free text landmark description, critical for rural/USSD cases."
    )
    address_text = models.CharField(max_length=255, blank=True)
    hospital_or_home = models.CharField(max_length=20, choices=HospitalOrHome.choices)
    institution = models.ForeignKey(
        "dioceses.Institution",
        on_delete=models.SET_NULL,
        related_name="sacrament_requests",
        null=True,
        blank=True,
    )

    family_contact_name = models.CharField(max_length=200, blank=True)
    family_contact_phone = models.CharField(max_length=20, blank=True)

    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.SUBMITTED)
    assigned_priest = models.ForeignKey(
        "clergy.PriestProfile",
        on_delete=models.SET_NULL,
        related_name="assigned_requests",
        null=True,
        blank=True,
    )
    assigned_parish = models.ForeignKey(
        "dioceses.Parish",
        on_delete=models.SET_NULL,
        related_name="routed_requests",
        null=True,
        blank=True,
    )

    channel = models.CharField(max_length=30, choices=RequestChannel.choices)

    # Logistics only (e.g. "gate code 4521") - never confession/spiritual content.
    logistics_notes = models.TextField(blank=True, max_length=1000)

    submitted_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-submitted_at"]
        indexes = [
            gis_models.Index(fields=["location"], name="request_location_gix"),
            models.Index(fields=["status", "emergency_level"], name="request_status_emerg_idx"),
        ]

    def __str__(self):
        return f"{self.tracking_code} - {self.sacrament_type} ({self.status})"


class RequestStatusEvent(TimeStampedModel):
    request = models.ForeignKey(SacramentRequest, on_delete=models.CASCADE, related_name="timeline")
    from_status = models.CharField(max_length=20, choices=RequestStatus.choices, blank=True)
    to_status = models.CharField(max_length=20, choices=RequestStatus.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.request.tracking_code}: {self.from_status} -> {self.to_status}"
