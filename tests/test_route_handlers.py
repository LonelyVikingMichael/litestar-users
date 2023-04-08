from unittest.mock import ANY

import pytest
from litestar.testing import TestClient
from pydantic import SecretStr

from starlite_users import StarliteUsersConfig

from .conftest import User, password_manager
from .utils import MockAuth


@pytest.mark.usefixtures("mock_user_repository")
def test_login(client: TestClient) -> None:
    success_response = client.post("/login", json={"email": "admin@example.com", "password": "iamsuperadmin"})
    assert success_response.status_code == 201

    fail_response = client.post("/login", json={"email": "admin@example.com", "password": "ijustguessed"})
    assert fail_response.status_code == 401


@pytest.mark.usefixtures("mock_user_repository")
def test_logout(client: TestClient, generic_user: User, starlite_users_config: StarliteUsersConfig) -> None:
    client.set_session_data({"user_id": str(generic_user.id)})
    response = client.post("/logout")
    if starlite_users_config.auth_backend != "session":
        assert response.status_code == 404
    else:
        assert response.status_code == 201
        assert client.get_session_data().get("user_id") is None


@pytest.mark.usefixtures("mock_user_repository")
def test_get_current_user(client: TestClient, generic_user: User, mock_auth: MockAuth) -> None:
    mock_auth.authenticate(generic_user.id)
    response = client.get("/users/me")
    assert response.status_code == 200


@pytest.mark.usefixtures("mock_user_repository")
def test_update_current_user(client: TestClient, generic_user: User, mock_auth: MockAuth) -> None:
    mock_auth.authenticate(generic_user.id)
    response = client.put("/users/me", json={"email": "updated@example.com"})
    assert response.status_code == 200
    assert generic_user.email == "updated@example.com"


@pytest.mark.usefixtures("mock_user_repository")
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


@pytest.mark.usefixtures("mock_user_repository")
def test_verification(client: TestClient, unverified_user: User, unverified_user_token: str) -> None:
    response = client.post("/verify", params={"token": unverified_user_token})
    assert response.status_code == 201
    response_body = response.json()
    assert response_body["id"] == str(unverified_user.id)
    assert response_body["is_verified"] is True


@pytest.mark.usefixtures("mock_user_repository")
def test_forgot_password(client: TestClient, generic_user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    response = client.post("/forgot-password", json={"email": generic_user.email})
    assert response.status_code == 201


@pytest.mark.usefixtures("mock_user_repository")
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
    assert password_manager.verify_and_update(SecretStr(PASSWORD), generic_user.password_hash)[0] is True
