import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.core.enums import UserRole
from apps.core.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestMemberRegistration:
    def test_register_creates_member_role_regardless_of_input(self):
        client = APIClient()
        response = client.post(
            "/api/accounts/register/",
            {
                "username": "newmember",
                "email": "newmember@example.com",
                "first_name": "New",
                "last_name": "Member",
                "phone_number": "+254700000010",
                "password": "TestPass123!",
                "role": "priest",  # must be ignored - never client-settable
            },
            format="json",
        )
        assert response.status_code == 201
        user = User.objects.get(username="newmember")
        assert user.role == UserRole.MEMBER

    def test_register_rejects_short_password(self):
        client = APIClient()
        response = client.post(
            "/api/accounts/register/",
            {
                "username": "shortpw",
                "phone_number": "+254700000011",
                "password": "short",
            },
            format="json",
        )
        assert response.status_code == 400


class TestJWTAuth:
    def test_token_obtain_embeds_role_claim(self):
        UserFactory(username="tokenuser", role=UserRole.MEMBER, password="TestPass123!")
        client = APIClient()
        response = client.post(
            "/api/accounts/auth/token/",
            {"username": "tokenuser", "password": "TestPass123!"},
            format="json",
        )
        assert response.status_code == 200
        assert "access" in response.data

        import jwt

        payload = jwt.decode(response.data["access"], options={"verify_signature": False})
        assert payload["role"] == UserRole.MEMBER

    def test_wrong_password_rejected(self):
        UserFactory(username="wrongpw", password="TestPass123!")
        client = APIClient()
        response = client.post(
            "/api/accounts/auth/token/",
            {"username": "wrongpw", "password": "incorrect"},
            format="json",
        )
        assert response.status_code == 401


class TestCustomUserManager:
    def test_createsuperuser_gets_super_admin_role(self):
        user = User.objects.create_superuser(
            username="rootadmin", email="root@example.com", password="TestPass123!", phone_number="+254700000012"
        )
        assert user.role == UserRole.SUPER_ADMIN
        assert user.is_superuser is True

    def test_regular_user_defaults_to_member_role(self):
        user = UserFactory()
        assert user.role == UserRole.MEMBER
