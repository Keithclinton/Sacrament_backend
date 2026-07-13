import pytest

from apps.core.factories import DioceseFactory

pytestmark = pytest.mark.django_db


class TestDiocesePublicListing:
    def test_diocese_list_is_public(self, client):
        DioceseFactory(name="Archdiocese of Nairobi")
        response = client.get("/api/dioceses/")
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_diocese_write_actions_still_require_super_admin(self, client):
        response = client.post("/api/dioceses/", {"name": "New Diocese", "code": "NEW"})
        assert response.status_code in (401, 403)
