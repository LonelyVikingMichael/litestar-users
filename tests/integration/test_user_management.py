from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.testing import TestClient

from tests.utils import MockAuth

if TYPE_CHECKING:
    from tests.integration.conftest import User


def test_get_current_user(client: TestClient, generic_user: User, mock_auth: MockAuth) -> None:
    mock_auth.authenticate(generic_user.id)
    response = client.get("/users/me")
    assert response.status_code == 200


def test_update_current_user(client: TestClient, generic_user: User, mock_auth: MockAuth) -> None:
    mock_auth.authenticate(generic_user.id)
    response = client.patch("/users/me", json={"username": "updated"})
    assert response.status_code == 200
    assert response.json()["username"] == "updated"
