from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.enums import VerificationStatus
from apps.core.models import TimeStampedModel

from .validators import ALLOWED_ATTESTATION_DOCUMENT_EXTENSIONS, validate_attestation_document_size


class PriestProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="priest_profile"
    )
    diocese = models.ForeignKey(
        "dioceses.Diocese", on_delete=models.PROTECT, related_name="priests"
    )
    parish = models.ForeignKey(
        "dioceses.Parish",
        on_delete=models.SET_NULL,
        related_name="priests",
        null=True,
        blank=True,
        help_text="Nullable at signup; required once verified.",
    )

    diocesan_id_number = models.CharField(max_length=100)
    ordination_date = models.DateField(null=True, blank=True)
    official_church_email = models.EmailField(blank=True)
    parish_attestation_document = models.FileField(
        upload_to="clergy/attestations/",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_ATTESTATION_DOCUMENT_EXTENSIONS),
            validate_attestation_document_size,
        ],
    )

    verification_status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING
    )
    verification_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="priest_verifications_performed",
        null=True,
        blank=True,
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    current_location = gis_models.PointField(geography=True, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    coverage_radius_km = models.FloatField(default=15)
    ministry_phone_number = models.CharField(max_length=20, blank=True)

    class Meta:
        indexes = [gis_models.Index(fields=["current_location"], name="priest_location_gix")]

    def __str__(self):
        return f"Fr. {self.user.get_full_name() or self.user.username} ({self.verification_status})"


class PriestVerificationEvent(TimeStampedModel):
    priest_profile = models.ForeignKey(
        PriestProfile, on_delete=models.CASCADE, related_name="verification_events"
    )
    from_status = models.CharField(max_length=20, choices=VerificationStatus.choices)
    to_status = models.CharField(max_length=20, choices=VerificationStatus.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.priest_profile} : {self.from_status} -> {self.to_status}"
