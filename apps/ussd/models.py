from django.db import models

from apps.core.models import TimeStampedModel


class USSDSession(TimeStampedModel):
    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    phone_number = models.CharField(max_length=20)
    current_step = models.CharField(max_length=50, default="init")
    collected_data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    last_interaction_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.session_id} ({self.phone_number}) @ {self.current_step}"
