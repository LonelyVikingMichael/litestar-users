from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Generator
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from litestar import Litestar
from litestar.contrib.jwt.jwt_token import Token
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig
from litestar.middleware.session.server_side import (
    ServerSideSessionConfig,
)
from litestar.testing import TestClient

from litestar_users import LitestarUsersConfig
from litestar_users.adapter.sqlalchemy.mixins import SQLAlchemyUserMixin
from litestar_users.password import PasswordManager
from litestar_users.service import BaseUserService

from .constants import ENCODING_SECRET, HASH_SCHEMES
from .utils import MockAuth

if TYPE_CHECKING:
    from collections.abc import Iterator

pytest_plugins = ["tests.docker_service_fixtures"]
password_manager = PasswordManager(hash_schemes=HASH_SCHEMES)


class User(UUIDBase, SQLAlchemyUserMixin):
    pass


class UserService(BaseUserService[User, Any]):  # pyright: ignore
    pass


@pytest.fixture()
def admin_user() -> User:
    return User(
        id=UUID("01676112-d644-4f93-ab32-562850e89549"),
        email="admin@example.com",
        password_hash=password_manager.hash("iamsuperadmin"),
        is_active=True,
        is_verified=True,
    )


@pytest.fixture()
def generic_user() -> User:
    return User(
        id=UUID("555d9ddb-7033-4819-a983-e817237b88e5"),
        email="good@example.com",
        password_hash=password_manager.hash("justauser"),
        is_active=True,
        is_verified=True,
    )


@pytest.fixture()
def generic_user_password_reset_token(generic_user: User) -> str:
    token = Token(
        exp=datetime.now() + timedelta(seconds=60 * 60 * 24),
        sub=str(generic_user.id),
        aud="reset_password",
    )
    return token.encode(secret=ENCODING_SECRET, algorithm="HS256")


@pytest.fixture()
def unverified_user() -> User:
    return User(
        id=UUID("68dec058-b752-42eb-8e55-b94a7b275f99"),
        email="unverified@example.com",
        password_hash=password_manager.hash("notveryverified"),
        is_active=True,
        is_verified=False,
    )


@pytest.fixture()
def unverified_user_token(unverified_user: User) -> str:
    token = Token(
        exp=datetime.now() + timedelta(seconds=60 * 60 * 24),
        sub=str(unverified_user.id),
        aud="verify",
    )
    return token.encode(secret=ENCODING_SECRET, algorithm="HS256")


@pytest.fixture()
def client(app: Litestar) -> "Iterator[TestClient]":
    with TestClient(app=app, session_config=ServerSideSessionConfig()) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def _patch_sqlalchemy_plugin_config() -> "Iterator":
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(SQLAlchemyAsyncConfig, "on_shutdown", MagicMock())
    yield
    monkeypatch.undo()


@pytest.fixture()
def mock_auth(client: TestClient, litestar_users_config: LitestarUsersConfig) -> MockAuth:
    return MockAuth(client=client, config=litestar_users_config)


@pytest.fixture()
def authenticate_admin(mock_auth: MockAuth, admin_user: User) -> Generator:
    mock_auth.authenticate(admin_user.id)
    yield


@pytest.fixture()
def authenticate_generic(mock_auth: MockAuth, generic_user: User) -> Generator:
    mock_auth.authenticate(generic_user.id)
    yield
