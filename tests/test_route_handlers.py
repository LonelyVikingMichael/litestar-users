import pytest
from starlite.testing import TestClient


@pytest.mark.usefixtures('mock_user_repository')
def test_login(client: TestClient) -> None:
    success_response = client.post('/login', json={'email': 'admin@example.com', 'password': 'iamsuperadmin'})
    assert success_response.status_code == 201

    fail_response = client.post('/login', json={'email': 'admin@example.com', 'password': 'ijustguessed'})
    assert fail_response.status_code == 401


@pytest.mark.usefixtures('mock_user_repository')
def test_get_current_user(client: TestClient) -> None:
    client.set_session_data({'user_id': '01676112-d644-4f93-ab32-562850e89549'})
    response = client.get('/users/me')
    assert response.status_code == 200
