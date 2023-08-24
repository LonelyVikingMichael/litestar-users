from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY

import pytest
from litestar.contrib.repository.exceptions import ConflictError

if TYPE_CHECKING:
    from litestar.testing import TestClient

    from tests.conftest import User


class TestRegistration:
    def test_basic_registration(self, client: TestClient) -> None:
        response = client.post("/register", json={"email": "someone@example.com", "password": "something"})
        assert response.status_code == 201
        assert response.json() == {
            "id": ANY,
            "email": "someone@example.com",
            "is_active": True,
            "is_verified": False,
        }

    def test_unique_email(self, client: TestClient, generic_user: User) -> None:
        with pytest.raises(ConflictError):
            response = client.post("/register", json={"email": generic_user.email, "password": "copycat"})
            assert response.status_code == 409

    def test_unsafe_fields_unset(self, client: TestClient) -> None:
        response = client.post(
            "/register",
            json={
                "email": "someone@example.com",
                "password": "something",
                "is_active": False,
                "is_verified": True,
            },
        )
        assert response.status_code == 201
        assert response.json() == {
            "id": ANY,
            "email": "someone@example.com",
            "is_active": True,
            "is_verified": False,
        }
