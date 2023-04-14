from typing import TYPE_CHECKING, Any, Optional

import uvicorn
from litestar import Litestar
from litestar.contrib.sqlalchemy.base import Base
from litestar.contrib.sqlalchemy.init_plugin import SQLAlchemyInitPlugin
from litestar.contrib.sqlalchemy.init_plugin.config import SQLAlchemyAsyncConfig
from litestar.exceptions import NotAuthorizedException
from pydantic import SecretStr
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column

from starlite_users import StarliteUsers, StarliteUsersConfig
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
    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler

ENCODING_SECRET = "1234567890abcdef"  # noqa: S105
DATABASE_URL = "sqlite+aiosqlite:///"
password_manager = PasswordManager()


class User(SQLAlchemyUserMixin):
    title = mapped_column(String(20))
    login_count = mapped_column(Integer(), default=0)


class UserCreateDTO(BaseUserCreateDTO):
    title: str


class UserReadDTO(BaseUserReadDTO):
    title: str
    login_count: int


class UserUpdateDTO(BaseUserUpdateDTO):
    title: Optional[str]
    # we'll update `login_count` in UserService.post_login_hook


class UserService(BaseUserService[User, UserCreateDTO, UserUpdateDTO, Any]):
    async def post_login_hook(self, user: User) -> None:  # This will properly increment the user's `login_count`
        user.login_count += 1  # pyright: ignore
        await self.user_repository.session.commit()


def example_authorization_guard(connection: "ASGIConnection", _: "BaseRouteHandler") -> None:
    """Authorize a request if the user's email string contains 'admin'."""
    if "admin" in connection.user.email:  # Don't do this in production
        return
    raise NotAuthorizedException()


sqlalchemy_config = SQLAlchemyAsyncConfig(connection_string=DATABASE_URL, session_dependency_key="session",)


async def on_startup() -> None:
    """Initialize the database."""
    async with sqlalchemy_config.create_engine().begin() as conn:  # pyright: ignore
        await conn.run_sync(Base.metadata.create_all)

    admin_user = User(
        email="admin@example.com",
        password_hash=password_manager.hash(SecretStr("iamsuperadmin")),
        is_active=True,
        is_verified=True,
        title="Exemplar",
    )
    session_maker = sqlalchemy_config.create_session_maker()
    async with session_maker() as session:
        async with session.begin():
            session.add(admin_user)


starlite_users = StarliteUsers(
    config=StarliteUsersConfig(
        auth_backend="session",
        secret=ENCODING_SECRET,  # type: ignore[arg-type]
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
)

app = Litestar(
    debug=True,
    on_app_init=[starlite_users.on_app_init],
    on_startup=[on_startup],
    plugins=[SQLAlchemyInitPlugin(config=sqlalchemy_config)],
    route_handlers=[],
)

if __name__ == "__main__":
    uvicorn.run(app="basic:app", reload=True)
