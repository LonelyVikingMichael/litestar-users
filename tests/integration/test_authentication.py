from litestar.testing import TestClient

from litestar_users import LitestarUsersConfig
from tests.conftest import User


def test_login(client: TestClient) -> None:
    success_response = client.post("/login", json={"email": "admin@example.com", "password": "iamsuperadmin"})
    assert success_response.status_code == 201

    fail_response = client.post("/login", json={"email": "admin@example.com", "password": "ijustguessed"})
    assert fail_response.status_code == 401


def test_logout(client: TestClient, generic_user: User, litestar_users_config: LitestarUsersConfig) -> None:
    client.set_session_data({"user_id": str(generic_user.id)})
    response = client.post("/logout")
    if litestar_users_config.auth_backend != "session":
        assert response.status_code == 404
    else:
        assert response.status_code == 201
        assert client.get_session_data().get("user_id") is None
