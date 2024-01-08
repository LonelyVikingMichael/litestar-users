from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.testing import TestClient

if TYPE_CHECKING:
    from tests.integration.conftest import User


def test_verification(client: TestClient, unverified_user: User, unverified_user_token: str) -> None:
    response = client.post("/verify", params={"token": unverified_user_token})
    assert response.status_code == 201
    response_body = response.json()
    assert response_body["id"] == str(unverified_user.id)
    assert response_body["is_verified"] is True
