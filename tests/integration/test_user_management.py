from litestar.testing import TestClient

from tests.conftest import User
from tests.utils import MockAuth


def test_get_current_user(client: TestClient, generic_user: User, mock_auth: MockAuth) -> None:
    mock_auth.authenticate(generic_user.id)
    response = client.get("/users/me")
    assert response.status_code == 200


def test_update_current_user(client: TestClient, generic_user: User, mock_auth: MockAuth) -> None:
    mock_auth.authenticate(generic_user.id)
    response = client.put("/users/me", json={"email": "updated@example.com"})
    assert response.status_code == 200
    assert response.json()["email"] == "updated@example.com"
