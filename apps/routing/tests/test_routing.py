import pytest
from django.contrib.gis.geos import Point

from apps.core.enums import VerificationStatus
from apps.core.factories import DioceseFactory, ParishFactory, PriestProfileFactory
from apps.routing.models import RequestEscalation
from apps.routing.services import escalate_request, find_nearest_available_priests

pytestmark = pytest.mark.django_db(transaction=True)

NAIROBI_CBD = Point(36.8172, -1.2841, srid=4326)
# ~480km away (Mombasa) - well outside the largest default radius tier (120km)
FAR_AWAY = Point(39.6682, -4.0435, srid=4326)


class TestNearestPriestMatching:
    def test_finds_closest_verified_available_priest_first(self):
        diocese = DioceseFactory()
        near = PriestProfileFactory(
            diocese=diocese, verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=Point(36.8180, -1.2830, srid=4326),
        )
        far = PriestProfileFactory(
            diocese=diocese, verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=Point(36.9000, -1.3200, srid=4326),
        )
        results = find_nearest_available_priests(NAIROBI_CBD)
        assert results[0].id == near.id
        assert far.id in [r.id for r in results]

    def test_excludes_unverified_priests(self):
        DioceseFactory()
        PriestProfileFactory(
            verification_status=VerificationStatus.PENDING, is_available=True,
            current_location=Point(36.8180, -1.2830, srid=4326),
        )
        results = find_nearest_available_priests(NAIROBI_CBD)
        assert results == []

    def test_excludes_unavailable_priests(self):
        PriestProfileFactory(
            verification_status=VerificationStatus.VERIFIED, is_available=False,
            current_location=Point(36.8180, -1.2830, srid=4326),
        )
        results = find_nearest_available_priests(NAIROBI_CBD)
        assert results == []

    def test_excludes_priests_outside_max_radius_tier(self):
        PriestProfileFactory(
            verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=FAR_AWAY,
        )
        results = find_nearest_available_priests(NAIROBI_CBD)
        assert results == []

    def test_exclude_ids_filters_out_already_tried_priests(self):
        priest = PriestProfileFactory(
            verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=Point(36.8180, -1.2830, srid=4326),
        )
        results = find_nearest_available_priests(NAIROBI_CBD, exclude_ids=[priest.id])
        assert results == []


class TestEscalation:
    @pytest.fixture(autouse=True)
    def _disable_eager_escalation_timeout(self, monkeypatch):
        """
        CELERY_TASK_ALWAYS_EAGER (test settings) makes apply_async(countdown=...)
        run immediately instead of actually waiting, which would race these
        tests' own manual escalate_request() calls with an auto-fired timeout.
        Neuter the scheduling call here; the timeout task's guard logic is
        covered directly in TestEscalationTimeoutTask below.
        """
        from apps.routing import tasks

        monkeypatch.setattr(tasks.check_escalation_timeout, "apply_async", lambda *args, **kwargs: None)

    def test_escalate_creates_next_level_and_excludes_prior_priest(self):
        diocese = DioceseFactory()
        parish = ParishFactory(diocese=diocese)
        first_priest = PriestProfileFactory(
            diocese=diocese, parish=parish, verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=Point(36.8180, -1.2830, srid=4326),
        )
        second_priest = PriestProfileFactory(
            diocese=diocese, parish=parish, verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=Point(36.8190, -1.2835, srid=4326),
        )

        from apps.core.enums import EmergencyLevel, HospitalOrHome, SacramentType
        from apps.requests_app.services import create_sacrament_request

        req = create_sacrament_request(
            data={
                "requester_name": "Jane",
                "requester_phone": "+254700000060",
                "patient_name": "Patient",
                "sacrament_type": SacramentType.LAST_RITES,
                "emergency_level": EmergencyLevel.EMERGENCY_DANGER_OF_DEATH,
                "location_description": "Test",
                "hospital_or_home": HospitalOrHome.HOSPITAL,
                "logistics_notes": "",
                "latitude": -1.2841,
                "longitude": 36.8172,
            },
            channel="web",
        )
        req.refresh_from_db()
        first_escalation = req.escalations.order_by("-escalation_level").first()
        assert first_escalation.escalated_to_priest_id == first_priest.id

        escalate_request(req, reason="priest_declined")
        escalations = list(req.escalations.order_by("escalation_level"))
        assert len(escalations) == 2
        assert escalations[1].escalated_to_priest_id == second_priest.id
        assert escalations[1].escalation_level == 1
        # prior escalation should be marked resolved once superseded
        escalations[0].refresh_from_db()
        assert escalations[0].resolved_at is not None

    def test_escalation_stops_after_max_levels(self, settings):
        settings.MAX_ESCALATION_LEVELS = 0
        diocese = DioceseFactory()
        parish = ParishFactory(diocese=diocese)
        PriestProfileFactory(
            diocese=diocese, parish=parish, verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=Point(36.8180, -1.2830, srid=4326),
        )

        from apps.core.enums import EmergencyLevel, HospitalOrHome, SacramentType
        from apps.requests_app.services import create_sacrament_request

        req = create_sacrament_request(
            data={
                "requester_name": "Jane",
                "requester_phone": "+254700000061",
                "patient_name": "Patient",
                "sacrament_type": SacramentType.LAST_RITES,
                "emergency_level": EmergencyLevel.EMERGENCY_DANGER_OF_DEATH,
                "location_description": "Test",
                "hospital_or_home": HospitalOrHome.HOSPITAL,
                "logistics_notes": "",
                "latitude": -1.2841,
                "longitude": 36.8172,
            },
            channel="web",
        )
        escalate_request(req, reason="priest_declined")
        # MAX_ESCALATION_LEVELS=0 means no further escalation rows beyond the initial routing
        assert RequestEscalation.objects.filter(request=req).count() == 1


class TestEscalationTimeoutTask:
    """
    Exercises check_escalation_timeout's own guard logic by calling the task
    body directly (bypassing apply_async/countdown/eager-mode entirely), so
    these assertions hold regardless of how Celery is configured to run.
    """

    def _routed_request(self):
        diocese = DioceseFactory()
        parish = ParishFactory(diocese=diocese)
        PriestProfileFactory(
            diocese=diocese, parish=parish, verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=Point(36.8180, -1.2830, srid=4326),
        )

        from apps.core.enums import EmergencyLevel, HospitalOrHome, SacramentType
        from apps.requests_app.services import create_sacrament_request

        return create_sacrament_request(
            data={
                "requester_name": "Jane",
                "requester_phone": "+254700000062",
                "patient_name": "Patient",
                "sacrament_type": SacramentType.LAST_RITES,
                "emergency_level": EmergencyLevel.EMERGENCY_DANGER_OF_DEATH,
                "location_description": "Test",
                "hospital_or_home": HospitalOrHome.HOSPITAL,
                "logistics_notes": "",
                "latitude": -1.2841,
                "longitude": 36.8172,
            },
            channel="web",
        )

    def test_noop_when_request_already_accepted(self, monkeypatch):
        from apps.routing import tasks
        from apps.routing.services import cancel_pending_escalation
        from apps.requests_app.services import accept_request

        monkeypatch.setattr(tasks.check_escalation_timeout, "apply_async", lambda *a, **k: None)
        req = self._routed_request()
        priest = req.escalations.first().escalated_to_priest
        accept_request(sacrament_request=req, priest_profile=priest)
        cancel_pending_escalation(req)

        before = RequestEscalation.objects.filter(request=req).count()
        tasks.check_escalation_timeout(str(req.id), 0)
        assert RequestEscalation.objects.filter(request=req).count() == before

    def test_noop_when_already_resolved(self, monkeypatch):
        from apps.routing import tasks
        from apps.routing.services import cancel_pending_escalation

        monkeypatch.setattr(tasks.check_escalation_timeout, "apply_async", lambda *a, **k: None)
        req = self._routed_request()
        cancel_pending_escalation(req)  # simulate the escalation being resolved out-of-band

        before = RequestEscalation.objects.filter(request=req).count()
        tasks.check_escalation_timeout(str(req.id), 0)
        assert RequestEscalation.objects.filter(request=req).count() == before

    def test_fires_escalation_when_still_unresolved(self, monkeypatch):
        from apps.routing import tasks

        monkeypatch.setattr(tasks.check_escalation_timeout, "apply_async", lambda *a, **k: None)
        req = self._routed_request()
        # A second available priest so the fired escalation has somewhere to go.
        PriestProfileFactory(
            diocese=req.assigned_parish.diocese, parish=req.assigned_parish,
            verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=Point(36.8190, -1.2835, srid=4326),
        )

        tasks.check_escalation_timeout(str(req.id), 0)
        escalations = list(req.escalations.order_by("escalation_level"))
        assert len(escalations) == 2
        assert escalations[1].reason == "no_response_timeout"


class TestLocationGeocodingFallback:
    def test_matches_known_institution_name_within_free_text(self):
        from apps.dioceses.models import Institution
        from apps.routing.geocoding import resolve_location_from_description

        diocese = DioceseFactory()
        institution = Institution.objects.create(
            name="Kenyatta National Hospital",
            institution_type="hospital",
            diocese=diocese,
            location=Point(36.8073, -1.3011, srid=4326),
        )
        resolved = resolve_location_from_description("Ward 4, Kenyatta National Hospital, near the gate")
        assert resolved is not None
        assert resolved.coords == institution.location.coords

    def test_matches_known_parish_name(self):
        diocese = DioceseFactory()
        parish = ParishFactory(diocese=diocese, name="Holy Family Basilica")
        from apps.routing.geocoding import resolve_location_from_description

        resolved = resolve_location_from_description("near Holy Family Basilica, Nairobi CBD")
        assert resolved.coords == parish.location.coords

    def test_no_match_returns_none(self):
        from apps.routing.geocoding import resolve_location_from_description

        assert resolve_location_from_description("some random unrecognized place") is None

    def test_empty_description_returns_none(self):
        from apps.routing.geocoding import resolve_location_from_description

        assert resolve_location_from_description("") is None
        assert resolve_location_from_description("   ") is None

    def test_ussd_request_with_recognizable_landmark_gets_routed(self):
        diocese = DioceseFactory()
        parish = ParishFactory(diocese=diocese, name="St. Peter's Parish", location=Point(36.8172, -1.2841, srid=4326))
        PriestProfileFactory(
            diocese=diocese, parish=parish, verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=Point(36.8175, -1.2845, srid=4326),
        )

        from apps.core.enums import EmergencyLevel, HospitalOrHome, SacramentType
        from apps.requests_app.services import create_sacrament_request

        req = create_sacrament_request(
            data={
                "requester_name": "Jane",
                "requester_phone": "+254700000070",
                "patient_name": "Patient",
                "sacrament_type": SacramentType.CONFESSION,
                "emergency_level": EmergencyLevel.ROUTINE,
                "location_description": "Right next to St. Peter's Parish",
                "hospital_or_home": HospitalOrHome.HOME,
                "logistics_notes": "",
            },
            channel="ussd",
        )
        req.refresh_from_db()
        assert req.status == "routed"
        assert req.location is not None


class TestWorkloadAwareMatching:
    def _assign_active_request(self, priest_profile, status="accepted"):
        from apps.requests_app.models import SacramentRequest
        from apps.requests_app.services import _generate_tracking_code

        return SacramentRequest.objects.create(
            tracking_code=_generate_tracking_code(),
            requester_name="Filler",
            requester_phone="+254700000099",
            patient_name="Filler Patient",
            sacrament_type="confession",
            emergency_level="routine",
            hospital_or_home="home",
            channel="web",
            status=status,
            assigned_priest=priest_profile,
        )

    def test_prefers_idle_farther_priest_over_busy_nearer_one(self, settings):
        settings.WORKLOAD_PENALTY_METERS_PER_ACTIVE_REQUEST = 5000
        diocese = DioceseFactory()
        busy_nearby = PriestProfileFactory(
            diocese=diocese, verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=Point(36.8173, -1.2842, srid=4326),  # ~15m from NAIROBI_CBD
        )
        idle_farther = PriestProfileFactory(
            diocese=diocese, verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=Point(36.8200, -1.2870, srid=4326),  # ~3.6km from NAIROBI_CBD
        )
        self._assign_active_request(busy_nearby, status="accepted")

        results = find_nearest_available_priests(NAIROBI_CBD)
        assert results[0].id == idle_farther.id

    def test_completed_requests_do_not_count_toward_workload(self, settings):
        settings.WORKLOAD_PENALTY_METERS_PER_ACTIVE_REQUEST = 5000
        diocese = DioceseFactory()
        priest = PriestProfileFactory(
            diocese=diocese, verification_status=VerificationStatus.VERIFIED, is_available=True,
            current_location=Point(36.8173, -1.2842, srid=4326),
        )
        self._assign_active_request(priest, status="completed")
        self._assign_active_request(priest, status="cancelled")

        results = find_nearest_available_priests(NAIROBI_CBD)
        assert results[0].id == priest.id
        assert results[0].active_request_count == 0
