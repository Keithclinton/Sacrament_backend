import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.clergy.services import transition_priest_verification
from apps.core.enums import UserRole, VerificationStatus
from apps.core.factories import DiocesanAdminProfileFactory, DioceseFactory, PriestProfileFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestVerificationStateMachine:
    def test_pending_to_verified_requires_under_review_first(self):
        priest = PriestProfileFactory(verification_status=VerificationStatus.PENDING)
        super_admin = UserFactory(role=UserRole.SUPER_ADMIN)

        with pytest.raises(ValidationError):
            transition_priest_verification(priest_profile=priest, to_status=VerificationStatus.VERIFIED, actor=super_admin)

    def test_full_happy_path_pending_to_verified(self):
        priest = PriestProfileFactory(verification_status=VerificationStatus.PENDING)
        super_admin = UserFactory(role=UserRole.SUPER_ADMIN)

        transition_priest_verification(priest_profile=priest, to_status=VerificationStatus.UNDER_REVIEW, actor=super_admin)
        priest.refresh_from_db()
        assert priest.verification_status == VerificationStatus.UNDER_REVIEW

        transition_priest_verification(priest_profile=priest, to_status=VerificationStatus.VERIFIED, actor=super_admin)
        priest.refresh_from_db()
        assert priest.verification_status == VerificationStatus.VERIFIED
        assert priest.verified_by == super_admin
        assert priest.verified_at is not None

    def test_rejection_requires_notes(self):
        priest = PriestProfileFactory(verification_status=VerificationStatus.UNDER_REVIEW)
        super_admin = UserFactory(role=UserRole.SUPER_ADMIN)

        with pytest.raises(ValidationError):
            transition_priest_verification(
                priest_profile=priest, to_status=VerificationStatus.REJECTED, actor=super_admin, notes=""
            )

        transition_priest_verification(
            priest_profile=priest, to_status=VerificationStatus.REJECTED, actor=super_admin, notes="ID mismatch"
        )
        priest.refresh_from_db()
        assert priest.verification_status == VerificationStatus.REJECTED

    def test_diocesan_admin_cannot_manage_priest_in_other_diocese(self):
        diocese_a = DioceseFactory()
        diocese_b = DioceseFactory()
        priest = PriestProfileFactory(diocese=diocese_b, verification_status=VerificationStatus.PENDING)
        admin_a = DiocesanAdminProfileFactory(diocese=diocese_a).user

        with pytest.raises(PermissionDenied):
            transition_priest_verification(
                priest_profile=priest, to_status=VerificationStatus.UNDER_REVIEW, actor=admin_a
            )

    def test_diocesan_admin_can_manage_priest_in_own_diocese(self):
        diocese = DioceseFactory()
        priest = PriestProfileFactory(diocese=diocese, verification_status=VerificationStatus.PENDING)
        admin = DiocesanAdminProfileFactory(diocese=diocese).user

        transition_priest_verification(priest_profile=priest, to_status=VerificationStatus.UNDER_REVIEW, actor=admin)
        priest.refresh_from_db()
        assert priest.verification_status == VerificationStatus.UNDER_REVIEW

    def test_only_super_admin_can_reinstate_suspended_priest(self):
        diocese = DioceseFactory()
        priest = PriestProfileFactory(diocese=diocese, verification_status=VerificationStatus.SUSPENDED)
        diocesan_admin = DiocesanAdminProfileFactory(diocese=diocese).user
        super_admin = UserFactory(role=UserRole.SUPER_ADMIN)

        with pytest.raises(PermissionDenied):
            transition_priest_verification(
                priest_profile=priest, to_status=VerificationStatus.VERIFIED, actor=diocesan_admin
            )

        transition_priest_verification(priest_profile=priest, to_status=VerificationStatus.VERIFIED, actor=super_admin)
        priest.refresh_from_db()
        assert priest.verification_status == VerificationStatus.VERIFIED

    def test_invalid_transition_rejected(self):
        priest = PriestProfileFactory(verification_status=VerificationStatus.REJECTED)
        super_admin = UserFactory(role=UserRole.SUPER_ADMIN)

        with pytest.raises(ValidationError):
            transition_priest_verification(priest_profile=priest, to_status=VerificationStatus.VERIFIED, actor=super_admin)


class TestPriestRegistrationAPI:
    def test_priest_self_registration_starts_pending(self, client):
        diocese = DioceseFactory()
        response = client.post(
            "/api/clergy/priests/register/",
            {
                "username": "frnew",
                "email": "frnew@example.com",
                "first_name": "New",
                "last_name": "Priest",
                "phone_number": "+254700000020",
                "password": "TestPass123!",
                "diocese": diocese.id,
                "diocesan_id_number": "NEW-001",
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["verification_status"] == VerificationStatus.PENDING

    def test_priest_registration_cannot_set_verification_status(self, client):
        diocese = DioceseFactory()
        response = client.post(
            "/api/clergy/priests/register/",
            {
                "username": "frsneaky",
                "email": "frsneaky@example.com",
                "first_name": "Sneaky",
                "last_name": "Priest",
                "phone_number": "+254700000021",
                "password": "TestPass123!",
                "diocese": diocese.id,
                "diocesan_id_number": "SNEAKY-001",
                "verification_status": "verified",
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["verification_status"] == VerificationStatus.PENDING


class TestAttestationDocumentUpload:
    def test_rejects_disallowed_file_extension(self):
        from django.core.exceptions import ValidationError as DjangoValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile

        priest = PriestProfileFactory()
        priest.parish_attestation_document = SimpleUploadedFile("malware.exe", b"not a real document")
        with pytest.raises(DjangoValidationError):
            priest.full_clean()

    def test_rejects_oversized_file(self):
        from django.core.exceptions import ValidationError as DjangoValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.clergy.validators import MAX_ATTESTATION_DOCUMENT_SIZE_BYTES

        priest = PriestProfileFactory()
        priest.parish_attestation_document = SimpleUploadedFile(
            "attestation.pdf", b"x" * (MAX_ATTESTATION_DOCUMENT_SIZE_BYTES + 1)
        )
        with pytest.raises(DjangoValidationError):
            priest.full_clean()

    def test_accepts_valid_pdf(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        priest = PriestProfileFactory()
        priest.parish_attestation_document = SimpleUploadedFile("attestation.pdf", b"small valid file")
        priest.full_clean()  # should not raise


class TestPriestSelfProfile:
    def test_has_location_false_until_priest_shares_it(self, client):
        priest = PriestProfileFactory(current_location=None)
        client.force_login(priest.user)

        response = client.get("/api/clergy/priests/me/")
        assert response.status_code == 200
        assert response.json()["has_location"] is False

        response = client.patch(
            "/api/clergy/priests/me/",
            {"latitude": -1.2841, "longitude": 36.8172},
            content_type="application/json",
        )
        assert response.status_code == 200
        priest.refresh_from_db()
        assert priest.current_location is not None

        response = client.get("/api/clergy/priests/me/")
        assert response.json()["has_location"] is True
