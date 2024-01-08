from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.testing import TestClient

if TYPE_CHECKING:
    from tests.integration.conftest import User


def test_forgot_password(client: TestClient, generic_user: User) -> None:
    response = client.post("/forgot-password", json={"email": generic_user.email})
    assert response.status_code == 201


def test_reset_password(client: TestClient, generic_user: User, generic_user_password_reset_token: str) -> None:
    PASSWORD = "veryverystrong123"
    response = client.post(
        "/reset-password",
        json={
            "token": generic_user_password_reset_token,
            "password": PASSWORD,
        },
    )
    assert response.status_code == 201
