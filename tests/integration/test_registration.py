from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY

if TYPE_CHECKING:
    from litestar.testing import TestClient

    from tests.integration.conftest import User


class TestRegistration:
    def test_basic_registration(self, client: TestClient) -> None:
        response = client.post(
            "/register", json={"email": "someone@example.com", "username": "generic", "password": "something"}
        )
        assert response.status_code == 201
        assert response.json() == {
            "id": ANY,
            "email": "someone@example.com",
            "username": "generic",
            "is_active": True,
            "is_verified": False,
        }

    def test_unique_identifier(self, client: TestClient, generic_user: User) -> None:
        response = client.post(
            "/register", json={"email": "some@one.com", "username": generic_user.username, "password": "copycat"}
        )
        assert response.status_code == 409

    def test_unsafe_fields_unset(self, client: TestClient) -> None:
        response = client.post(
            "/register",
            json={
                "email": "danger@there.com",
                "username": "king",
                "password": "something",
                "is_active": False,
                "is_verified": True,
            },
        )
        assert response.status_code == 201
        assert response.json() == {
            "id": ANY,
            "email": "danger@there.com",
            "username": "king",
            "is_active": True,
            "is_verified": False,
        }
