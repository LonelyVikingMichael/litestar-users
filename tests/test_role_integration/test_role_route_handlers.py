from typing import TYPE_CHECKING
from unittest.mock import ANY

import pytest

if TYPE_CHECKING:
    from starlite.testing import TestClient

    from .conftest import Role, User


@pytest.mark.usefixtures("mock_user_repository")
class TestRoleManagement:
    @pytest.mark.usefixtures("authenticate_admin")
    def test_create_role(self, client: "TestClient") -> None:
        response = client.post("/users/roles", json={"name": "editor", "description": "..."})
        assert response.status_code == 201
        assert response.json() == {
            "id": ANY,
            "name": "editor",
            "description": "...",
        }

    @pytest.mark.usefixtures("authenticate_admin")
    def test_update_role(self, client: "TestClient", writer_role: "Role") -> None:
        response = client.put(f"/users/roles/{writer_role.id}", json={"name": "editor"})
        assert response.status_code == 200
        assert response.json() == {
            "id": str(writer_role.id),
            "name": "editor",
            "description": writer_role.description,
        }
        assert writer_role.name == "editor"

    @pytest.mark.usefixtures("authenticate_admin")
    def test_delete_role(self, client: "TestClient", writer_role: "Role") -> None:
        response = client.delete(f"/users/roles/{writer_role.id}")
        assert response.status_code == 204

    @pytest.mark.usefixtures("authenticate_admin")
    def test_assign_role(self, client: "TestClient", generic_user: "User", writer_role: "Role") -> None:
        response = client.patch(
            "/users/roles/assign", json={"user_id": str(generic_user.id), "role_id": str(writer_role.id)}
        )
        assert response.status_code == 200
        assert generic_user.roles == [writer_role]

    @pytest.mark.usefixtures("authenticate_admin")
    def test_revoke_role(self, client: "TestClient", admin_user: "User", admin_role: "Role") -> None:
        response = client.patch(
            "/users/roles/revoke", json={"user_id": str(admin_user.id), "role_id": str(admin_role.id)}
        )
        assert response.status_code == 200
        assert admin_user.roles == []
