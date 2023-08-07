from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator
from uuid import UUID

import pytest
from litestar import Litestar
from litestar.contrib.jwt.jwt_token import Token
from litestar.contrib.repository.exceptions import RepositoryError
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig, SQLAlchemyInitPlugin
from litestar.contrib.sqlalchemy.plugins.init.config.asyncio import AsyncSessionConfig
from litestar.middleware.session.server_side import (
    ServerSideSessionConfig,
)
from litestar.testing import TestClient
from pydantic import SecretStr
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from litestar_users import LitestarUsers, LitestarUsersConfig
from litestar_users.adapter.sqlalchemy.mixins import SQLAlchemyUserMixin
from litestar_users.config import (
    AuthHandlerConfig,
    CurrentUserHandlerConfig,
    PasswordResetHandlerConfig,
    RegisterHandlerConfig,
    UserManagementHandlerConfig,
    VerificationHandlerConfig,
)
from litestar_users.exceptions import TokenException, repository_exception_to_http_response, token_exception_handler
from litestar_users.password import PasswordManager
from litestar_users.schema import BaseUserCreateDTO, BaseUserUpdateDTO
from litestar_users.service import BaseUserService
from tests.constants import ENCODING_SECRET, HASH_SCHEMES
from tests.utils import MockAuth, basic_guard

if TYPE_CHECKING:
    from collections import abc


UUIDBase.metadata.clear()
password_manager = PasswordManager(hash_schemes=HASH_SCHEMES)
here = Path(__file__).parent


@pytest.fixture(scope="session")
def event_loop() -> "abc.Iterator[asyncio.AbstractEventLoop]":
    """Scoped Event loop.

    Need the event loop scoped to the session so that we can use it to check
    containers are ready in session scoped containers fixture.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


class User(UUIDBase, SQLAlchemyUserMixin):
    pass


class UserService(BaseUserService[User, BaseUserCreateDTO, BaseUserUpdateDTO, Any]):  # pyright: ignore
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


@pytest.fixture()
def sqlalchemy_plugin_config(docker_ip: str) -> SQLAlchemyAsyncConfig:
    return SQLAlchemyAsyncConfig(
        connection_string=f"postgresql+asyncpg://postgres:super-secret@{docker_ip}:5423/postgres",
        session_dependency_key="session",
        session_config=AsyncSessionConfig(expire_on_commit=False),
    )


@pytest.fixture()
def sqlalchemy_plugin(sqlalchemy_plugin_config: SQLAlchemyAsyncConfig) -> SQLAlchemyInitPlugin:
    return SQLAlchemyInitPlugin(config=sqlalchemy_plugin_config)


@pytest.fixture(
    params=[
        pytest.param("session", id="session"),
        pytest.param("jwt", id="jwt"),
        pytest.param("jwt_cookie", id="jwt_cookie"),
    ],
)
def litestar_users_config(
    request: pytest.FixtureRequest, sqlalchemy_plugin_config: SQLAlchemyAsyncConfig
) -> LitestarUsersConfig:
    return LitestarUsersConfig(  # pyright: ignore
        auth_backend=request.param,
        session_backend_config=ServerSideSessionConfig(),
        secret=ENCODING_SECRET,
        sqlalchemy_plugin_config=sqlalchemy_plugin_config,
        user_model=User,  # pyright: ignore
        user_service_class=UserService,
        auth_handler_config=AuthHandlerConfig(),
        current_user_handler_config=CurrentUserHandlerConfig(),
        password_reset_handler_config=PasswordResetHandlerConfig(),
        register_handler_config=RegisterHandlerConfig(),
        user_management_handler_config=UserManagementHandlerConfig(guards=[basic_guard]),
        verification_handler_config=VerificationHandlerConfig(),
    )


@pytest.fixture()
def litestar_users(litestar_users_config: LitestarUsersConfig) -> LitestarUsers:
    return LitestarUsers(config=litestar_users_config)


@pytest.fixture()
def app(litestar_users: LitestarUsers, sqlalchemy_plugin: SQLAlchemyInitPlugin) -> Litestar:
    return Litestar(
        debug=True,
        exception_handlers={
            RepositoryError: repository_exception_to_http_response,  # type: ignore[dict-item]
            TokenException: token_exception_handler,  # type: ignore[dict-item]
        },
        on_app_init=[litestar_users.on_app_init],
        plugins=[sqlalchemy_plugin],
        route_handlers=[],
    )


# @pytest.fixture()
# async def client(app: Litestar) -> AsyncIterator[AsyncClient]:
#     """Async client that calls requests on the app.

#     ```text
#     ValueError: The future belongs to a different loop than the one specified as the loop argument
#     ```
#     """
#     async with AsyncClient(app=app, base_url="http://testserver.local") as client_:
#         yield client_


@pytest.fixture()
def client(app: Litestar) -> "Iterator[TestClient]":
    with TestClient(app=app, session_config=ServerSideSessionConfig()) as client:
        yield client


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


@pytest.fixture(scope="session")
def docker_compose_file() -> Path:
    """Load docker compose file.

    Returns:
        Path to the docker-compose file for end-to-end test environment.
    """
    return here / "docker-compose.yml"


@pytest.fixture(name="engine")
async def fx_engine(docker_ip: str, postgres_service: None) -> AsyncEngine:
    """Postgresql instance for end-to-end testing.

    Args:
        docker_ip: IP address for TCP connection to Docker containers.

    Returns:
        Async SQLAlchemy engine instance.
    """
    return create_async_engine(
        URL(
            drivername="postgresql+asyncpg",
            username="postgres",
            password="super-secret",
            host=docker_ip,
            port=5423,
            database="postgres",
            query={},  # pyright: ignore
        ),
        echo=False,
        poolclass=NullPool,
    )


@pytest.fixture(autouse=True)
def _patch_db(
    app: Litestar, engine: AsyncEngine, sqlalchemy_plugin: SQLAlchemyInitPlugin, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(app.state, sqlalchemy_plugin._config.engine_app_state_key, engine)
    monkeypatch.setitem(
        app.state, sqlalchemy_plugin._config.session_maker_app_state_key, async_sessionmaker(bind=engine)
    )


@pytest.fixture()
def sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture()
def session(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncSession:
    return sessionmaker()


@pytest.fixture(autouse=True)
async def _seed_db(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    admin_user: User,
    generic_user: User,
    unverified_user: User,
) -> AsyncIterator[None]:
    """Populate test database with.

    Args:
        engine: The SQLAlchemy engine instance.
        sessionmaker: The SQLAlchemy sessionmaker factory.
        raw_users: Test users to add to the database
    """

    metadata = User.metadata
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    async with sessionmaker() as session:
        session.add_all([admin_user, generic_user, unverified_user])
        await session.commit()
    yield
