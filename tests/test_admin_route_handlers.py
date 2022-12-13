from unittest.mock import ANY

import pytest
from starlite.testing import TestClient

from .conftest import User

GENERIC_USER_DICT = {
    'id': ANY,
    'email': 'good@example.com',
    'is_active': True,
    'is_verified': True,
    'roles': [],
}

@pytest.mark.usefixtures('mock_user_repository')
def test_get_user_as_admin(client: TestClient, admin_user: User, generic_user: User) -> None:
    client.set_session_data({'user_id': str(admin_user.id)})
    response = client.get(f'/users/{generic_user.id}')
    assert response.status_code == 200
    assert response.json() == GENERIC_USER_DICT


@pytest.mark.usefixtures('mock_user_repository')
def test_get_user_as_generic(client: TestClient, admin_user: User, generic_user: User) -> None:
    client.set_session_data({'user_id': str(generic_user.id)})
    response = client.get(f'/users/{admin_user.id}')
    assert response.status_code == 401


@pytest.mark.usefixtures('mock_user_repository')
def test_update_user_as_admin(client: TestClient, admin_user: User, generic_user: User) -> None:
    client.set_session_data({'user_id': str(admin_user.id)})
    response = client.put(f'/users/{generic_user.id}', json={'email': 'robust@example.com'})
    assert response.status_code == 200
    assert generic_user.email == 'robust@example.com'


@pytest.mark.usefixtures('mock_user_repository')
def test_update_user_as_generic(client: TestClient, admin_user: User, generic_user: User) -> None:
    client.set_session_data({'user_id': str(generic_user.id)})
    response = client.put(f'/users/{admin_user.id}', json={'email': 'wrong@example.com'})
    assert response.status_code == 401


@pytest.mark.usefixtures('mock_user_repository')
def test_delete_user_as_admin(client: TestClient, admin_user: User, generic_user: User) -> None:
    client.set_session_data({'user_id': str(admin_user.id)})
    response = client.delete(f'/users/{generic_user.id}')
    assert response.status_code == 204


@pytest.mark.usefixtures('mock_user_repository')
def test_delete_user_as_generic(client: TestClient, admin_user: User, generic_user: User) -> None:
    client.set_session_data({'user_id': str(generic_user.id)})
    response = client.delete(f'/users/{admin_user.id}')
    assert response.status_code == 401
