from datetime import timedelta

from celery import shared_task
from django.utils import timezone


@shared_task
def cleanup_stale_ussd_sessions():
    """Periodic housekeeping: AT expires sessions itself, but stale rows here
    are useful for debugging abandoned USSD flows."""
    from .models import USSDSession

    cutoff = timezone.now() - timedelta(minutes=5)
    USSDSession.objects.filter(is_active=True, last_interaction_at__lt=cutoff).update(is_active=False)
