from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, Generic, Iterator, Optional, Type
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base
from starlite import Starlite
from starlite.contrib.jwt.jwt_token import Token
from starlite.middleware.session.memory_backend import MemoryBackendConfig
from starlite.plugins.sql_alchemy import SQLAlchemyConfig, SQLAlchemyPlugin
from starlite.testing import TestClient

from starlite_users import StarliteUsersConfig, StarliteUsersPlugin
from starlite_users.adapter.sqlalchemy.models import (
    SQLAlchemyRoleModel,
    SQLAlchemyUserModel,
    UserRoleAssociation,
)
from starlite_users.config import (
    AuthHandlerConfig,
    CurrentUserHandlerConfig,
    PasswordResetHandlerConfig,
    RegisterHandlerConfig,
    UserManagementHandlerConfig,
    VerificationHandlerConfig,
)
from starlite_users.exceptions import UserNotFoundException
from starlite_users.password import PasswordManager
from starlite_users.schema import UserReadDTO
from starlite_users.service import UserModelType, UserService

from .constants import ENCODING_SECRET
from .utils import MockAuth

if TYPE_CHECKING:
    from collections.abc import Iterator


class _Base:
    """Base for all SQLAlchemy models."""

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        unique=True,
        nullable=False,
    )


Base = declarative_base(cls=_Base)
password_manager = PasswordManager()


class User(Base, SQLAlchemyUserModel):
    pass


class Role(Base, SQLAlchemyRoleModel):
    pass


class UserRole(Base, UserRoleAssociation):
    pass


class MyUserService(UserService):
    model_type = User
    secret = SecretStr(ENCODING_SECRET)


@pytest.fixture()
def admin_role() -> Role:
    return Role(
        id=UUID("9b62b52c-4278-4124-aca8-783ab281c196"),
        name="administrator",
        description="X",
    )


@pytest.fixture()
def admin_user(admin_role: Role) -> User:
    return User(
        id=UUID("01676112-d644-4f93-ab32-562850e89549"),
        email="admin@example.com",
        password_hash=password_manager.get_hash(SecretStr("iamsuperadmin")),
        is_active=True,
        is_verified=True,
        roles=[admin_role],
    )


@pytest.fixture()
def generic_user() -> User:
    return User(
        id=UUID("555d9ddb-7033-4819-a983-e817237b88e5"),
        email="good@example.com",
        password_hash=password_manager.get_hash(SecretStr("justauser")),
        is_active=True,
        is_verified=True,
        roles=[],
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
        password_hash=password_manager.get_hash(SecretStr("notveryverified")),
        is_active=True,
        is_verified=False,
        roles=[],
    )


@pytest.fixture()
def unverified_user_token(unverified_user: User) -> str:
    token = Token(
        exp=datetime.now() + timedelta(seconds=60 * 60 * 24),
        sub=str(unverified_user.id),
        aud="verify",
    )
    return token.encode(secret=ENCODING_SECRET, algorithm="HS256")


class MockSQLAlchemyUserRepository(Generic[UserModelType]):
    store = {}

    def __init__(self, model_type: Type[UserModelType], **kwargs: Any) -> None:
        self.model_type = model_type

    async def add(self, data: UserModelType) -> UserModelType:
        data.id = uuid4()
        self.store[data.id] = data
        return data

    async def get(self, id_: UUID) -> Optional[UserModelType]:
        result = self.store.get(str(id_))
        if result is None:
            raise UserNotFoundException
        return result

    async def get_by(self, **kwargs: Any) -> Optional[UserModelType]:
        for user in self.store.values():
            if all([getattr(user, key) == kwargs[key] for key in kwargs.keys()]):
                return user

    async def update(self, id_: UUID, data: Dict[str, Any]) -> UserModelType:
        result = await self.get(id_)
        for k, v in data.items():
            setattr(result, k, v)
        return result

    async def delete(self, id_: UUID) -> None:
        del self.store[str(id_)]


@pytest.fixture(
    scope="module",
    params=[
        pytest.param("session", id="session"),
        pytest.param("jwt", id="jwt"),
        pytest.param("jwt_cookie", id="jwt_cookie"),
    ],
)
def plugin_config(request: pytest.FixtureRequest) -> StarliteUsersConfig:
    return StarliteUsersConfig(
        auth_backend=request.param,
        secret=ENCODING_SECRET,
        session_backend_config=MemoryBackendConfig(),
        user_model=User,
        user_read_dto=UserReadDTO,
        user_service_class=MyUserService,
        auth_handler_config=AuthHandlerConfig(),
        current_user_handler_config=CurrentUserHandlerConfig(),
        password_reset_handler_config=PasswordResetHandlerConfig(),
        register_handler_config=RegisterHandlerConfig(),
        user_management_handler_config=UserManagementHandlerConfig(),
        verification_handler_config=VerificationHandlerConfig(),
    )


@pytest.fixture()
def plugin(plugin_config: StarliteUsersConfig) -> StarliteUsersPlugin:
    return StarliteUsersPlugin(config=plugin_config)


@pytest.fixture()
def app(plugin: StarliteUsersPlugin) -> Starlite:
    return Starlite(
        debug=True,
        on_app_init=[plugin.on_app_init],
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
    UserRepository = MockSQLAlchemyUserRepository[User]
    store = {
        str(admin_user.id): admin_user,
        str(generic_user.id): generic_user,
        str(unverified_user.id): unverified_user,
    }
    monkeypatch.setattr(UserRepository, "store", store)
    monkeypatch.setattr("starlite_users.service.SQLAlchemyUserRepository", UserRepository)


@pytest.fixture()
def mock_auth(client: TestClient, plugin_config: StarliteUsersConfig) -> MockAuth:
    return MockAuth(client=client, config=plugin_config)
