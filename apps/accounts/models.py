from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.contrib.gis.db import models as gis_models
from django.db import models

from apps.core.enums import UserRole
from apps.core.models import TimeStampedModel


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.SUPER_ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser, TimeStampedModel):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.MEMBER)
    phone_number = models.CharField(max_length=20, unique=True)
    preferred_language = models.CharField(max_length=10, default="en")

    # Optional, opt-in only: a persistent location for auto-filling requests.
    # Sensitive per-request location (e.g. a sick person's exact bedside) is
    # captured on the SacramentRequest itself, not stored here.
    last_known_location = gis_models.PointField(geography=True, null=True, blank=True)

    objects = UserManager()

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class DiocesanAdminProfile(TimeStampedModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="diocesan_admin_profile"
    )
    diocese = models.ForeignKey(
        "dioceses.Diocese", on_delete=models.PROTECT, related_name="admin_profiles"
    )

    def __str__(self):
        return f"{self.user} - {self.diocese}"
