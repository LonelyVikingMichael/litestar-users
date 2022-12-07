from typing import Any, Generic, Iterator, Optional, Type, TYPE_CHECKING
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from pydantic import SecretStr
import pytest
from starlite import Starlite
from starlite.middleware.session.memory_backend import MemoryBackendConfig
from starlite.plugins.sql_alchemy import SQLAlchemyPlugin, SQLAlchemyConfig
from starlite.testing import TestClient
from sqlalchemy import Column
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from starlite_users import StarliteUsersPlugin, StarliteUsersConfig
from starlite_users.service import UserModelType
from starlite_users.exceptions import UserNotFoundException
from starlite_users.models import SQLAlchemyUserModel, SQLAlchemyRoleModel, RoleUser as RoleUser_
from starlite_users.password import PasswordManager
from starlite_users.route_handlers import (
    get_auth_handler,
    get_current_user_handler,
    get_user_management_handler,
    get_registration_handler,
    get_verification_handler
)

if TYPE_CHECKING:
    from collections.abc import Iterator


class _Base:
    """Base for all SQLAlchemy models."""

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, nullable=False)


Base = declarative_base(cls=_Base)


class User(Base, SQLAlchemyUserModel):
    pass


class Role(Base, SQLAlchemyRoleModel):
    pass


class RoleUser(Base, RoleUser_):
    pass


password_manager = PasswordManager()

class MockSQLAlchemyUserRepository(Generic[UserModelType]):
    store = {}

    def __init__(self, model_type: Type[UserModelType], *args: Any, **kwargs: Any) -> None:
        self.model_type = model_type

    async def add(self, data: UserModelType) -> UserModelType:
        data.id = uuid4()
        self.store[data.id] = data
        return data

    async def get(self, id_: UUID) -> Optional[UserModelType]:
        result = self.store.get(id_)
        if result is None:
            raise UserNotFoundException
        return result

    async def get_by(self, **kwargs: Any) -> Optional[UserModelType]:
        for user in self.store.values():
            if all([getattr(user, key) == kwargs[key] for key in kwargs.keys()]):
                return user

    async def update(self, data: UserModelType) -> UserModelType:
        result = await self.get(data.id)
        for k, v in data.__dict__.items():
            if k.startswith('_'):
                continue
            setattr(result, k, v)
        return result

    async def delete(self, id_: UUID) -> None:
        del(self.store['id'])


@pytest.fixture()
def plugin() -> StarliteUsersPlugin:
    return StarliteUsersPlugin(
        config=StarliteUsersConfig(
            auth_strategy='session',
            session_backend_config=MemoryBackendConfig(),
            route_handlers=[
                get_auth_handler(),
                get_current_user_handler(),
                get_user_management_handler(),
                get_registration_handler(),
                get_verification_handler(),
            ],
            user_model=User,
        )
    )


@pytest.fixture()
def app(plugin: StarliteUsersPlugin) -> Starlite:
    return Starlite(
        debug=True,
        on_app_init=[plugin.on_app_init],
        plugins=[
            SQLAlchemyPlugin(
                config=SQLAlchemyConfig(
                    connection_string='postgresql+asyncpg:///',
                    dependency_key='session',
                )
            )
        ],
        route_handlers=[]
    )


@pytest.fixture()
def client(app: Starlite) -> 'Iterator[TestClient]':
    with TestClient(app=app, session_config=MemoryBackendConfig()) as client:
        yield client


@pytest.fixture(scope='session', autouse=True)
def _patch_sqlalchemy_plugin_config() -> 'Iterator':
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(SQLAlchemyConfig, 'on_shutdown', MagicMock())
    yield
    monkeypatch.undo()


admin_role = Role(id=UUID('9b62b52c-4278-4124-aca8-783ab281c196'), name='administrator', description='X')
administrator = User(
    id=UUID('01676112-d644-4f93-ab32-562850e89549'),
    email='admin@example.com',
    password_hash=password_manager.get_hash(SecretStr('iamsuperadmin')),
    roles=[admin_role],
)
generic_user = User(
    id=UUID('555d9ddb-7033-4819-a983-e817237b88e5'),
    email='good@example.com',
    password_hash=password_manager.get_hash(SecretStr('justauser')),
    roles=[],
)

@pytest.fixture()
def mock_user_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    UserRepository = MockSQLAlchemyUserRepository[User]
    store = {
        str(administrator.id): administrator,
        str(generic_user.id): generic_user
    }
    monkeypatch.setattr(UserRepository, 'store', store)
    monkeypatch.setattr('starlite_users.service.SQLAlchemyUserRepository', UserRepository)
