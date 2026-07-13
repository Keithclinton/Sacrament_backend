from django.contrib.gis.db import models as gis_models
from django.db import models

from apps.core.models import TimeStampedModel


class Diocese(TimeStampedModel):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    bishop_name = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    # Optional future geofencing; v1 relies on nearest-distance matching instead.
    boundary = gis_models.PolygonField(geography=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Deanery(TimeStampedModel):
    diocese = models.ForeignKey(Diocese, on_delete=models.CASCADE, related_name="deaneries")
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = ("diocese", "name")
        verbose_name_plural = "Deaneries"
        ordering = ["diocese", "name"]

    def __str__(self):
        return f"{self.name} ({self.diocese.code})"


class Parish(TimeStampedModel):
    diocese = models.ForeignKey(Diocese, on_delete=models.CASCADE, related_name="parishes")
    deanery = models.ForeignKey(
        Deanery, on_delete=models.SET_NULL, related_name="parishes", null=True, blank=True
    )
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True)
    location = gis_models.PointField(geography=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [gis_models.Index(fields=["location"], name="parish_location_gix")]

    def __str__(self):
        return self.name


class Institution(TimeStampedModel):
    """
    A hospital, chaplaincy, or care home - places with a location and
    (usually) an affiliated chaplain, sharing identical routing behaviour.
    """

    class InstitutionType(models.TextChoices):
        HOSPITAL = "hospital", "Hospital"
        CHAPLAINCY = "chaplaincy", "Chaplaincy"
        CARE_HOME = "care_home", "Care Home"

    name = models.CharField(max_length=200)
    institution_type = models.CharField(max_length=20, choices=InstitutionType.choices)
    diocese = models.ForeignKey(Diocese, on_delete=models.CASCADE, related_name="institutions")
    parish = models.ForeignKey(
        Parish, on_delete=models.SET_NULL, related_name="institutions", null=True, blank=True
    )
    location = gis_models.PointField(geography=True)
    assigned_chaplain = models.ForeignKey(
        "clergy.PriestProfile",
        on_delete=models.SET_NULL,
        related_name="chaplaincy_institutions",
        null=True,
        blank=True,
    )
    contact_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [gis_models.Index(fields=["location"], name="institution_location_gix")]

    def __str__(self):
        return f"{self.name} ({self.get_institution_type_display()})"
