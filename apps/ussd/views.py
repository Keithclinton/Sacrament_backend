import hmac

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .menu import handle_ussd_input
from .models import USSDSession

USSD_RATE_LIMIT = 30  # keypresses
USSD_RATE_WINDOW_SECONDS = 300  # per phone number, per 5 minutes - a full
# conversation is ~7 keypresses, so this comfortably allows retries/mistakes
# while still bounding abuse of the webhook.


def _is_rate_limited(phone_number: str) -> bool:
    if not phone_number:
        return False
    cache_key = f"ussd_rate:{phone_number}"
    count = cache.get(cache_key, 0)
    if count >= USSD_RATE_LIMIT:
        return True
    cache.set(cache_key, count + 1, timeout=USSD_RATE_WINDOW_SECONDS)
    return False


@method_decorator(csrf_exempt, name="dispatch")
class USSDWebhookView(View):
    """
    Africa's Talking POSTs sessionId/phoneNumber/serviceCode/text on every
    keypress. No JWT auth here - AT calls this directly, so it's secured via
    a shared secret query param instead (?secret=...), checked against
    USSD_SHARED_SECRET using a constant-time comparison (a naive `!=` would
    leak timing information an attacker could use to brute-force the secret).
    """

    def post(self, request):
        supplied_secret = request.GET.get("secret", "")
        if not hmac.compare_digest(supplied_secret, settings.USSD_SHARED_SECRET):
            return HttpResponseForbidden("Invalid secret.")

        session_id = request.POST.get("sessionId", "")
        phone_number = request.POST.get("phoneNumber", "")
        text = request.POST.get("text", "")

        if _is_rate_limited(phone_number):
            return HttpResponse("END Too many requests. Please try again later.", content_type="text/plain")

        session, _ = USSDSession.objects.get_or_create(
            session_id=session_id, defaults={"phone_number": phone_number}
        )
        response_text = handle_ussd_input(session, text)
        return HttpResponse(response_text, content_type="text/plain")
