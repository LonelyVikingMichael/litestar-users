from typing import TYPE_CHECKING, Any, Optional
from uuid import uuid4

import uvicorn
from pydantic import SecretStr
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm.decl_api import declarative_base
from starlite import NotAuthorizedException, OpenAPIConfig, Starlite
from starlite.middleware.session.memory_backend import MemoryBackendConfig
from starlite.plugins.sql_alchemy import SQLAlchemyConfig, SQLAlchemyPlugin

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
from starlite_users.schema import BaseUserCreateDTO, BaseUserReadDTO, BaseUserUpdateDTO
from starlite_users.service import BaseUserService

if TYPE_CHECKING:
    from starlite import ASGIConnection, BaseRouteHandler, Request

ENCODING_SECRET = "1234567890abcdef"  # noqa: S105
DATABASE_URL = "sqlite+aiosqlite:///"
password_manager = PasswordManager()


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


class User(Base, SQLAlchemyUserMixin):  # type: ignore[valid-type, misc]
    __tablename__ = "user"

    title = Column(String(20))
    login_count = Column(Integer(), default=0)


class UserCreateDTO(BaseUserCreateDTO):
    title: str


class UserReadDTO(BaseUserReadDTO):
    title: str
    login_count: int


class UserUpdateDTO(BaseUserUpdateDTO):
    title: Optional[str]
    # we'll update `login_count` in UserService.post_login_hook


class UserService(BaseUserService[User, UserCreateDTO, UserUpdateDTO, Any]):
    async def post_login_hook(self, user: User, request: "Optional[Request]") -> None:  # This will properly increment the user's `login_count`
        user.login_count += 1  # pyright: ignore
        await self.repository.session.commit()


def example_authorization_guard(connection: "ASGIConnection", _: "BaseRouteHandler") -> None:
    """Authorize a request if the user's email string contains 'admin'."""

    if "admin" in connection.user.email:  # Don't do this in production
        return
    raise NotAuthorizedException()


sqlalchemy_config = SQLAlchemyConfig(
    connection_string=DATABASE_URL,
    dependency_key="session",
)


async def on_startup() -> None:
    """Initialize the database."""
    async with sqlalchemy_config.engine.begin() as conn:  # pyright: ignore
        await conn.run_sync(Base.metadata.create_all)

    admin_user = User(
        email="admin@example.com",
        password_hash=password_manager.hash(SecretStr("iamsuperadmin")),
        is_active=True,
        is_verified=True,
        title="Exemplar",
    )

    async with sqlalchemy_config.session_maker() as session, session.begin():
        session.add(admin_user)


starlite_users_config = StarliteUsersConfig(
    auth_backend="session",
    secret=ENCODING_SECRET,  # type: ignore[arg-type]
    session_backend_config=MemoryBackendConfig(),
    user_model=User,
    user_read_dto=UserReadDTO,
    user_create_dto=UserCreateDTO,
    user_update_dto=UserUpdateDTO,
    user_service_class=UserService,  # pyright: ignore
    auth_handler_config=AuthHandlerConfig(),
    current_user_handler_config=CurrentUserHandlerConfig(),
    password_reset_handler_config=PasswordResetHandlerConfig(),
    register_handler_config=RegisterHandlerConfig(),
    user_management_handler_config=UserManagementHandlerConfig(guards=[example_authorization_guard]),
    verification_handler_config=VerificationHandlerConfig(),
)

starlite_users = StarliteUsers(config=starlite_users_config)

openapi_config = OpenAPIConfig(
    title="Starlite Users example API",
    version="1.0.0",
    security=[starlite_users_config.auth_config.security_requirement],
)

app = Starlite(
    debug=True,
    on_app_init=[starlite_users.on_app_init],
    on_startup=[on_startup],
    plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
    route_handlers=[],
    openapi_config=openapi_config,
)

if __name__ == "__main__":
    uvicorn.run(app="basic:app", reload=True)
