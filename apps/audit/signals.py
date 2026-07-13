from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.clergy.models import PriestVerificationEvent
from apps.requests_app.models import RequestStatusEvent

from .services import log_action


@receiver(post_save, sender=PriestVerificationEvent)
def log_priest_verification_event(sender, instance, created, **kwargs):
    if not created:
        return
    log_action(
        actor=instance.changed_by,
        action="priest_verification_changed",
        target=instance.priest_profile,
        metadata={"from_status": instance.from_status, "to_status": instance.to_status, "notes": instance.notes},
    )


@receiver(post_save, sender=RequestStatusEvent)
def log_request_status_event(sender, instance, created, **kwargs):
    if not created:
        return
    log_action(
        actor=instance.changed_by,
        action="request_status_changed",
        target=instance.request,
        metadata={"from_status": instance.from_status, "to_status": instance.to_status},
    )
