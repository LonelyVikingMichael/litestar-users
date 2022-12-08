from unittest.mock import ANY

import pytest
from starlite.testing import TestClient

from .conftest import User


@pytest.mark.usefixtures('mock_user_repository')
def test_login(client: TestClient) -> None:
    success_response = client.post('/login', json={'email': 'admin@example.com', 'password': 'iamsuperadmin'})
    assert success_response.status_code == 201

    fail_response = client.post('/login', json={'email': 'admin@example.com', 'password': 'ijustguessed'})
    assert fail_response.status_code == 401


@pytest.mark.usefixtures('mock_user_repository')
def test_logout(client: TestClient, generic_user: User) -> None:
    client.set_session_data({'user_id': str(generic_user.id)})
    response = client.post('/logout')
    assert response.status_code == 201
    assert client.get_session_data().get('user_id') is None


@pytest.mark.usefixtures('mock_user_repository')
def test_get_current_user(client: TestClient, generic_user: User) -> None:
    client.set_session_data({'user_id': str(generic_user.id)})
    response = client.get('/users/me')
    assert response.status_code == 200


@pytest.mark.usefixtures('mock_user_repository')
def test_update_current_user(client: TestClient, generic_user: User) -> None:
    client.set_session_data({'user_id': str(generic_user.id)})
    response = client.put('/users/me', json={'email': 'updated@example.com'})
    assert response.status_code == 200
    assert generic_user.email == 'updated@example.com'


@pytest.mark.usefixtures('mock_user_repository')
def test_registration(client: TestClient) -> None:
    response = client.post('/register', json={'email': 'someone@example.com', 'password': 'something'})
    assert response.status_code == 201
    assert response.json() == {
        'id': ANY,
        'email': 'someone@example.com',
        'roles': []
    }
