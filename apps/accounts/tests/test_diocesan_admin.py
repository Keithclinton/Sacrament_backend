import pytest

from apps.accounts.models import DiocesanAdminProfile, User
from apps.core.enums import UserRole
from apps.core.factories import DioceseFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestDiocesanAdminCreation:
    def test_super_admin_can_create_diocesan_admin(self, client):
        super_admin = UserFactory(role=UserRole.SUPER_ADMIN, password="TestPass123!")
        diocese = DioceseFactory()
        client.force_login(super_admin)

        response = client.post(
            "/api/accounts/diocesan-admins/",
            {
                "username": "newdiocesanadmin",
                "email": "admin@diocese.org",
                "first_name": "Diocesan",
                "last_name": "Admin",
                "phone_number": "+254700000030",
                "password": "TestPass123!",
                "diocese": diocese.id,
            },
            content_type="application/json",
        )
        assert response.status_code == 201
        user = User.objects.get(username="newdiocesanadmin")
        assert user.role == UserRole.DIOCESAN_ADMIN
        assert DiocesanAdminProfile.objects.filter(user=user, diocese=diocese).exists()

    def test_regular_member_cannot_create_diocesan_admin(self, client):
        member = UserFactory(role=UserRole.MEMBER, password="TestPass123!")
        diocese = DioceseFactory()
        client.force_login(member)

        response = client.post(
            "/api/accounts/diocesan-admins/",
            {
                "username": "sneakyadmin",
                "first_name": "Sneaky",
                "last_name": "Admin",
                "phone_number": "+254700000031",
                "password": "TestPass123!",
                "diocese": diocese.id,
            },
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_unauthenticated_cannot_create_diocesan_admin(self, client):
        diocese = DioceseFactory()
        response = client.post(
            "/api/accounts/diocesan-admins/",
            {
                "username": "anonadmin",
                "first_name": "Anon",
                "last_name": "Admin",
                "phone_number": "+254700000032",
                "password": "TestPass123!",
                "diocese": diocese.id,
            },
            content_type="application/json",
        )
        assert response.status_code in (401, 403)
