import pytest
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError

from apps.core.enums import HospitalOrHome, RequestStatus, SacramentType, EmergencyLevel, UserRole
from apps.core.factories import DiocesanAdminProfileFactory, DioceseFactory, ParishFactory, PriestProfileFactory, UserFactory
from apps.requests_app.models import SacramentRequest
from apps.requests_app.services import (
    accept_request,
    cancel_request,
    create_sacrament_request,
    decline_request,
)

# transaction=True: create_sacrament_request/notify() dispatch via
# transaction.on_commit, which never fires under the default (rolled-back)
# django_db transaction - real commits are needed to exercise that path.
pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def _clear_cache():
    # DRF's ScopedRateThrottle uses the real Redis cache, which persists
    # across tests unless cleared explicitly.
    cache.clear()
    yield
    cache.clear()


def _base_request_data(**overrides):
    data = {
        "requester_name": "Jane Doe",
        "requester_phone": "+254700000050",
        "patient_name": "Grandma Mary",
        "sacrament_type": SacramentType.ANOINTING_OF_THE_SICK,
        "emergency_level": EmergencyLevel.URGENT,
        "location_description": "Nairobi Hospital",
        "hospital_or_home": HospitalOrHome.HOSPITAL,
        "logistics_notes": "",
    }
    data.update(overrides)
    return data


class TestCreateSacramentRequest:
    def test_anonymous_request_has_null_requester(self):
        req = create_sacrament_request(data=_base_request_data(), channel="ussd", requester=None)
        assert req.requester is None
        assert req.tracking_code.startswith("SAC-")
        assert req.status in (RequestStatus.SUBMITTED, RequestStatus.ROUTED)

    def test_authenticated_request_links_requester(self):
        member = UserFactory()
        req = create_sacrament_request(data=_base_request_data(), channel="web", requester=member)
        assert req.requester == member

    def test_no_field_exists_for_confession_content(self):
        # By-design invariant: only logistics_notes exists for free text, nothing
        # resembling spiritual/confession content is a field on the model.
        field_names = {f.name for f in SacramentRequest._meta.get_fields()}
        assert "logistics_notes" in field_names
        forbidden = {"confession_content", "sin_details", "message", "conversation"}
        assert not (forbidden & field_names)

    def test_routes_to_nearest_verified_available_priest(self):
        diocese = DioceseFactory()
        parish = ParishFactory(diocese=diocese)
        priest = PriestProfileFactory(diocese=diocese, parish=parish, verification_status="verified", is_available=True)

        req = create_sacrament_request(
            data=_base_request_data(latitude=-1.2841, longitude=36.8172),
            channel="web",
        )
        req.refresh_from_db()
        assert req.status == RequestStatus.ROUTED
        assert req.assigned_parish == priest.parish

    def test_unverified_priest_never_matched(self):
        diocese = DioceseFactory()
        PriestProfileFactory(diocese=diocese, verification_status="pending", is_available=True)

        req = create_sacrament_request(data=_base_request_data(latitude=-1.2841, longitude=36.8172), channel="web")
        req.refresh_from_db()
        assert req.status == RequestStatus.SUBMITTED
        assert req.assigned_parish is None

    def test_no_gps_request_stays_submitted(self):
        req = create_sacrament_request(data=_base_request_data(), channel="ussd")
        req.refresh_from_db()
        assert req.status == RequestStatus.SUBMITTED


class TestAcceptDeclineFlow:
    def _routed_request(self):
        diocese = DioceseFactory()
        parish = ParishFactory(diocese=diocese)
        priest = PriestProfileFactory(diocese=diocese, parish=parish, verification_status="verified", is_available=True)
        req = create_sacrament_request(data=_base_request_data(latitude=-1.2841, longitude=36.8172), channel="web")
        req.refresh_from_db()
        return req, priest

    def test_priest_can_accept_routed_request(self):
        req, priest = self._routed_request()
        accept_request(sacrament_request=req, priest_profile=priest)
        req.refresh_from_db()
        assert req.status == RequestStatus.ACCEPTED
        assert req.assigned_priest == priest

    def test_cannot_accept_already_accepted_request(self):
        req, priest = self._routed_request()
        accept_request(sacrament_request=req, priest_profile=priest)
        with pytest.raises(ValidationError):
            accept_request(sacrament_request=req, priest_profile=priest)

    def test_decline_by_wrong_priest_denied(self):
        req, priest = self._routed_request()
        accept_request(sacrament_request=req, priest_profile=priest)
        other_priest = PriestProfileFactory(verification_status="verified")
        with pytest.raises(PermissionDenied):
            decline_request(sacrament_request=req, priest_profile=other_priest)


class TestCancelAndStatusTransitions:
    def test_cancel_from_submitted(self):
        req = create_sacrament_request(data=_base_request_data(), channel="ussd")
        actor = UserFactory()
        cancel_request(sacrament_request=req, actor=actor)
        req.refresh_from_db()
        assert req.status == RequestStatus.CANCELLED

    def test_cancel_after_completed_rejected(self):
        req = create_sacrament_request(data=_base_request_data(), channel="ussd")
        actor = UserFactory()
        cancel_request(sacrament_request=req, actor=actor)
        with pytest.raises(ValidationError):
            cancel_request(sacrament_request=req, actor=actor)


class TestObjectPermissions:
    def test_owner_can_view_own_request(self, client):
        member = UserFactory(password="TestPass123!")
        req = create_sacrament_request(data=_base_request_data(), channel="web", requester=member)
        client.force_login(member)
        response = client.get(f"/api/requests/{req.id}/")
        assert response.status_code == 200

    def test_other_member_cannot_view_someone_elses_request(self, client):
        owner = UserFactory(password="TestPass123!")
        stranger = UserFactory(password="TestPass123!")
        req = create_sacrament_request(data=_base_request_data(), channel="web", requester=owner)
        client.force_login(stranger)
        response = client.get(f"/api/requests/{req.id}/")
        assert response.status_code == 403

    def test_tracking_lookup_is_public(self, client):
        req = create_sacrament_request(data=_base_request_data(), channel="ussd")
        response = client.get(f"/api/requests/track/{req.tracking_code}/")
        assert response.status_code == 200
        assert response.json()["status"] == req.status


class TestPriestListView:
    @pytest.fixture(autouse=True)
    def _disable_eager_escalation_timeout(self, monkeypatch):
        # CELERY_TASK_ALWAYS_EAGER (test settings) makes apply_async(countdown=...)
        # run immediately instead of waiting, which would auto-resolve the
        # escalation this test is asserting is still pending. See the same
        # fixture in apps/routing/tests/test_routing.py for more detail.
        from apps.routing import tasks

        monkeypatch.setattr(tasks.check_escalation_timeout, "apply_async", lambda *args, **kwargs: None)

    def test_priest_sees_requests_awaiting_their_decision(self, client):
        diocese = DioceseFactory()
        parish = ParishFactory(diocese=diocese)
        priest = PriestProfileFactory(
            diocese=diocese, parish=parish, verification_status="verified", is_available=True,
        )
        req = create_sacrament_request(data=_base_request_data(latitude=-1.2841, longitude=36.8172), channel="web")
        req.refresh_from_db()
        assert req.status == RequestStatus.ROUTED  # routed to `priest`, not yet accepted

        client.force_login(priest.user)
        response = client.get("/api/requests/mine/")
        assert response.status_code == 200
        codes = [r["tracking_code"] for r in response.json()["results"]]
        assert req.tracking_code in codes

    def test_pending_offer_disappears_once_accepted(self):
        # Regression guard for the underlying query: once an escalation is
        # resolved (accepted), it must not still count as "pending".
        diocese = DioceseFactory()
        parish = ParishFactory(diocese=diocese)
        first_priest = PriestProfileFactory(
            diocese=diocese, parish=parish, verification_status="verified", is_available=True,
        )
        req = create_sacrament_request(data=_base_request_data(latitude=-1.2841, longitude=36.8172), channel="web")
        req.refresh_from_db()

        from apps.routing.services import get_pending_request_ids_for_priest

        assert req.id in list(get_pending_request_ids_for_priest(first_priest))

        accept_request(sacrament_request=req, priest_profile=first_priest)
        assert req.id not in list(get_pending_request_ids_for_priest(first_priest))


class TestCreateEndpointThrottling:
    def test_anonymous_creation_throttled_after_configured_rate(self, client, monkeypatch):
        from rest_framework.throttling import ScopedRateThrottle

        # SimpleRateThrottle.THROTTLE_RATES is bound to api_settings at class
        # definition time (a plain attribute, not a property), so overriding
        # settings.REST_FRAMEWORK at runtime has no effect on it - the class
        # attribute itself must be patched directly to change the rate in a test.
        monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"request_create": "2/hour", "request_track": "30/minute"})

        for _ in range(2):
            response = client.post("/api/requests/", _base_request_data(), content_type="application/json")
            assert response.status_code == 201

        response = client.post("/api/requests/", _base_request_data(), content_type="application/json")
        assert response.status_code == 429
