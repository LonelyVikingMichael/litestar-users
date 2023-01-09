from typing import TYPE_CHECKING
from unittest.mock import ANY

import pytest
from starlite.testing import TestClient

from .conftest import User

if TYPE_CHECKING:
    from .utils import MockAuth

GENERIC_USER_DICT = {
    "id": ANY,
    "email": "good@example.com",
    "is_active": True,
    "is_verified": True,
}


@pytest.mark.usefixtures("mock_user_repository")
class TestUserManagement:
    @pytest.mark.usefixtures("authenticate_admin")
    def test_get_user_as_admin(self, client: TestClient, generic_user: User) -> None:
        response = client.get(f"/users/{generic_user.id}")
        assert response.status_code == 200
        assert response.json() == GENERIC_USER_DICT

    def test_get_user_as_generic(
        self, client: TestClient, admin_user: User, generic_user: User, mock_auth: "MockAuth"
    ) -> None:
        mock_auth.authenticate(generic_user.id)
        response = client.get(f"/users/{admin_user.id}")
        assert response.status_code == 401

    def test_update_user_as_admin(
        self, client: TestClient, admin_user: User, generic_user: User, mock_auth: "MockAuth"
    ) -> None:
        mock_auth.authenticate(admin_user.id)
        response = client.put(f"/users/{generic_user.id}", json={"email": "robust@example.com"})
        assert response.status_code == 200
        assert generic_user.email == "robust@example.com"

    def test_update_user_as_generic(
        self, client: TestClient, admin_user: User, generic_user: User, mock_auth: "MockAuth"
    ) -> None:
        mock_auth.authenticate(generic_user.id)
        response = client.put(f"/users/{admin_user.id}", json={"email": "wrong@example.com"})
        assert response.status_code == 401

    def test_delete_user_as_admin(
        self, client: TestClient, admin_user: User, generic_user: User, mock_auth: "MockAuth"
    ) -> None:
        mock_auth.authenticate(admin_user.id)
        response = client.delete(f"/users/{generic_user.id}")
        assert response.status_code == 204

    def test_delete_user_as_generic(
        self, client: TestClient, admin_user: User, generic_user: User, mock_auth: "MockAuth"
    ) -> None:
        mock_auth.authenticate(generic_user.id)
        response = client.delete(f"/users/{admin_user.id}")
        assert response.status_code == 401
