from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Generator
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import Column
from sqlalchemy.orm.decl_api import declarative_base
from starlite import Starlite
from starlite.contrib.jwt.jwt_token import Token
from starlite.middleware.session.memory_backend import MemoryBackendConfig
from starlite.plugins.sql_alchemy import SQLAlchemyConfig, SQLAlchemyPlugin
from starlite.testing import TestClient

from starlite_users import StarliteUsers, StarliteUsersConfig
from starlite_users.adapter.sqlalchemy.guid import GUID
from starlite_users.adapter.sqlalchemy.mixins import SQLAlchemyUserMixin
from starlite_users.config import (
    AuthHandlerConfig,
    CurrentUserHandlerConfig,
    PasswordResetHandlerConfig,
    RegisterHandlerConfig,
    UserManagementHandlerConfig,
    VerificationHandlerConfig,
)
from starlite_users.password import PasswordManager
from starlite_users.schema import BaseUserCreateDTO, BaseUserUpdateDTO
from starlite_users.service import BaseUserService

from .constants import ENCODING_SECRET, HASH_SCHEMES
from .utils import MockAuth, MockSQLAlchemyUserRepository, basic_guard

if TYPE_CHECKING:
    from collections.abc import Iterator


class _Base:
    """Base for all SQLAlchemy models."""

    id = Column(
        GUID(),
        primary_key=True,
        default=uuid4,
        unique=True,
        nullable=False,
    )


Base = declarative_base(cls=_Base)
password_manager = PasswordManager(hash_schemes=HASH_SCHEMES)


class User(Base, SQLAlchemyUserMixin):  # type: ignore[valid-type, misc]
    __tablename__ = "user"


class UserService(BaseUserService[User, BaseUserCreateDTO, BaseUserUpdateDTO, Any]):
    pass


@pytest.fixture()
def admin_user() -> User:
    return User(
        id=UUID("01676112-d644-4f93-ab32-562850e89549"),
        email="admin@example.com",
        password_hash=password_manager.hash(SecretStr("iamsuperadmin")),
        is_active=True,
        is_verified=True,
    )


@pytest.fixture()
def generic_user() -> User:
    return User(
        id=UUID("555d9ddb-7033-4819-a983-e817237b88e5"),
        email="good@example.com",
        password_hash=password_manager.hash(SecretStr("justauser")),
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
    return token.encode(secret=ENCODING_SECRET.get_secret_value(), algorithm="HS256")


@pytest.fixture()
def unverified_user() -> User:
    return User(
        id=UUID("68dec058-b752-42eb-8e55-b94a7b275f99"),
        email="unverified@example.com",
        password_hash=password_manager.hash(SecretStr("notveryverified")),
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
    return token.encode(secret=ENCODING_SECRET.get_secret_value(), algorithm="HS256")


@pytest.fixture(
    scope="module",
    params=[
        pytest.param("session", id="session"),
        pytest.param("jwt", id="jwt"),
        pytest.param("jwt_cookie", id="jwt_cookie"),
    ],
)
def starlite_users_config(request: pytest.FixtureRequest) -> StarliteUsersConfig:
    return StarliteUsersConfig(  # pyright: ignore
        auth_backend=request.param,
        secret=ENCODING_SECRET,
        session_backend_config=MemoryBackendConfig(),
        user_model=User,
        user_service_class=UserService,
        auth_handler_config=AuthHandlerConfig(),
        current_user_handler_config=CurrentUserHandlerConfig(),
        password_reset_handler_config=PasswordResetHandlerConfig(),
        register_handler_config=RegisterHandlerConfig(),
        user_management_handler_config=UserManagementHandlerConfig(guards=[basic_guard]),
        verification_handler_config=VerificationHandlerConfig(),
    )


@pytest.fixture()
def starlite_users(starlite_users_config: StarliteUsersConfig) -> StarliteUsers:
    return StarliteUsers(config=starlite_users_config)


@pytest.fixture()
def app(starlite_users: StarliteUsers) -> Starlite:
    return Starlite(
        debug=True,
        on_app_init=[starlite_users.on_app_init],
        plugins=[
            SQLAlchemyPlugin(
                config=SQLAlchemyConfig(
                    connection_string="sqlite+aiosqlite:///",
                    dependency_key="session",
                )
            )
        ],
        route_handlers=[],
    )


@pytest.fixture()
def client(app: Starlite) -> "Iterator[TestClient]":
    with TestClient(app=app, session_config=MemoryBackendConfig()) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def _patch_sqlalchemy_plugin_config() -> "Iterator":
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(SQLAlchemyConfig, "on_shutdown", MagicMock())
    yield
    monkeypatch.undo()


@pytest.fixture()
def mock_user_repository(
    admin_user: User,
    generic_user: User,
    unverified_user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    UserRepository = MockSQLAlchemyUserRepository
    user_store = {
        str(admin_user.id): admin_user,
        str(generic_user.id): generic_user,
        str(unverified_user.id): unverified_user,
    }
    monkeypatch.setattr(UserRepository, "user_store", user_store)
    monkeypatch.setattr("starlite_users.user_handlers.SQLAlchemyUserRepository", UserRepository)
    monkeypatch.setattr("starlite_users.dependencies.SQLAlchemyUserRepository", UserRepository)


@pytest.fixture()
def mock_auth(client: TestClient, starlite_users_config: StarliteUsersConfig) -> MockAuth:
    return MockAuth(client=client, config=starlite_users_config)


@pytest.fixture()
def authenticate_admin(mock_auth: MockAuth, admin_user: User) -> Generator:
    mock_auth.authenticate(admin_user.id)
    yield


@pytest.fixture()
def authenticate_generic(mock_auth: MockAuth, generic_user: User) -> Generator:
    mock_auth.authenticate(generic_user.id)
    yield
