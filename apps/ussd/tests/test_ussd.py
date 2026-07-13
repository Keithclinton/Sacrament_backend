import pytest
from django.core.cache import cache

from apps.requests_app.models import SacramentRequest
from apps.ussd.models import USSDSession

pytestmark = pytest.mark.django_db(transaction=True)

WEBHOOK = "/api/ussd/webhook/"


@pytest.fixture(autouse=True)
def _clear_cache():
    # The rate limiter (and DRF throttling elsewhere) uses the real Redis
    # cache, which persists across tests unless cleared explicitly.
    cache.clear()
    yield
    cache.clear()


def _post(client, secret, session_id, phone, text):
    return client.post(
        f"{WEBHOOK}?secret={secret}",
        {"sessionId": session_id, "phoneNumber": phone, "text": text},
    )


class TestUSSDWebhookSecurity:
    def test_wrong_secret_rejected(self, client, settings):
        settings.USSD_SHARED_SECRET = "correct-secret"
        response = client.post(f"{WEBHOOK}?secret=wrong", {"sessionId": "s1", "phoneNumber": "+254711111111", "text": ""})
        assert response.status_code == 403

    def test_missing_secret_rejected(self, client, settings):
        settings.USSD_SHARED_SECRET = "correct-secret"
        response = client.post(WEBHOOK, {"sessionId": "s1", "phoneNumber": "+254711111111", "text": ""})
        assert response.status_code == 403


class TestUSSDRequestFlow:
    def test_full_conversation_creates_request(self, client, settings):
        settings.USSD_SHARED_SECRET = "test-secret"
        session_id = "session-full"
        phone = "+254722222222"

        r1 = _post(client, "test-secret", session_id, phone, "")
        assert r1.content.decode().startswith("CON")

        r2 = _post(client, "test-secret", session_id, phone, "1")
        assert "Select sacrament" in r2.content.decode()

        r3 = _post(client, "test-secret", session_id, phone, "1*4")
        assert "How urgent" in r3.content.decode()

        r4 = _post(client, "test-secret", session_id, phone, "1*4*1")
        assert "patient's name" in r4.content.decode()

        r5 = _post(client, "test-secret", session_id, phone, "1*4*1*Grandpa Joe")
        assert "location" in r5.content.decode().lower()

        r6 = _post(client, "test-secret", session_id, phone, "1*4*1*Grandpa Joe*Machakos Hospital")
        assert "phone number" in r6.content.decode().lower()

        r7 = _post(client, "test-secret", session_id, phone, "1*4*1*Grandpa Joe*Machakos Hospital*0")
        body = r7.content.decode()
        assert body.startswith("END")
        assert "Reference: SAC-" in body

        tracking_code = body.split("Reference: ")[1].split(".")[0]
        req = SacramentRequest.objects.get(tracking_code=tracking_code)
        assert req.channel == "ussd"
        assert req.patient_name == "Grandpa Joe"
        assert req.requester_phone == phone
        assert req.sacrament_type == "last_rites"
        assert req.emergency_level == "emergency_danger_of_death"

        session = USSDSession.objects.get(session_id=session_id)
        assert session.is_active is False

    def test_invalid_main_menu_choice_ends_session(self, client, settings):
        settings.USSD_SHARED_SECRET = "test-secret"
        _post(client, "test-secret", "s-invalid", "+254733333333", "")
        response = _post(client, "test-secret", "s-invalid", "+254733333333", "9")
        assert response.content.decode().startswith("END")

    def test_status_check_flow(self, client, settings):
        settings.USSD_SHARED_SECRET = "test-secret"
        from apps.requests_app.services import create_sacrament_request

        req = create_sacrament_request(
            data={
                "requester_name": "Someone",
                "requester_phone": "+254744444444",
                "patient_name": "Patient",
                "sacrament_type": "confession",
                "emergency_level": "routine",
                "location_description": "Somewhere",
                "hospital_or_home": "home",
                "logistics_notes": "",
            },
            channel="ussd",
        )

        _post(client, "test-secret", "s-track", "+254744444444", "")
        _post(client, "test-secret", "s-track", "+254744444444", "2")
        response = _post(client, "test-secret", "s-track", "+254744444444", f"2*{req.tracking_code}")
        assert "Submitted" in response.content.decode()

    def test_unknown_tracking_code_reports_not_found(self, client, settings):
        settings.USSD_SHARED_SECRET = "test-secret"
        _post(client, "test-secret", "s-notfound", "+254755555555", "")
        _post(client, "test-secret", "s-notfound", "+254755555555", "2")
        response = _post(client, "test-secret", "s-notfound", "+254755555555", "2*SAC-NOPE1")
        assert "No request found" in response.content.decode()


class TestUSSDRateLimiting:
    def test_same_phone_number_throttled_after_limit(self, client, settings, monkeypatch):
        settings.USSD_SHARED_SECRET = "test-secret"
        from apps.ussd import views as ussd_views

        monkeypatch.setattr(ussd_views, "USSD_RATE_LIMIT", 3)

        phone = "+254766666666"
        for i in range(3):
            response = _post(client, "test-secret", f"s-rate-{i}", phone, "")
            assert response.content.decode().startswith("CON")

        response = _post(client, "test-secret", "s-rate-over", phone, "")
        assert "Too many requests" in response.content.decode()

    def test_different_phone_numbers_are_not_cross_throttled(self, client, settings, monkeypatch):
        settings.USSD_SHARED_SECRET = "test-secret"
        from apps.ussd import views as ussd_views

        monkeypatch.setattr(ussd_views, "USSD_RATE_LIMIT", 1)

        _post(client, "test-secret", "s-a", "+254777777777", "")
        response = _post(client, "test-secret", "s-b", "+254788888888", "")
        assert response.content.decode().startswith("CON")
