from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import uvicorn
from advanced_alchemy.base import UUIDBase
from advanced_alchemy.config import AsyncSessionConfig
from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO, SQLAlchemyDTOConfig
from advanced_alchemy.extensions.litestar.plugins import SQLAlchemyAsyncConfig, SQLAlchemyInitPlugin
from litestar import Litestar, Request
from litestar.dto import DataclassDTO
from litestar.exceptions import NotAuthorizedException
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.security.session_auth import SessionAuth
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from litestar_users import LitestarUsersConfig, LitestarUsersPlugin
from litestar_users.adapter.sqlalchemy.mixins import SQLAlchemyUserMixin
from litestar_users.config import (
    AuthHandlerConfig,
    CurrentUserHandlerConfig,
    PasswordResetHandlerConfig,
    RegisterHandlerConfig,
    UserManagementHandlerConfig,
    VerificationHandlerConfig,
)
from litestar_users.password import PasswordManager
from litestar_users.service import BaseUserService

if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler

ENCODING_SECRET = "1234567890abcdef"  # noqa: S105
DATABASE_URL = "sqlite+aiosqlite:///"
password_manager = PasswordManager()

UUIDBase.metadata.clear()


class User(UUIDBase, SQLAlchemyUserMixin):
    title: Mapped[str] = mapped_column(String(20))
    login_count: Mapped[int] = mapped_column(Integer(), default=0)


@dataclass
class UserRegistrationSchema:
    email: str
    password: str
    title: str


class UserRegistrationDTO(DataclassDTO[UserRegistrationSchema]):
    """User registration DTO."""


class UserReadDTO(SQLAlchemyDTO[User]):
    config = SQLAlchemyDTOConfig(exclude={"login_count"})


class UserUpdateDTO(SQLAlchemyDTO[User]):
    # we'll update `login_count` in UserService.post_login_hook
    config = SQLAlchemyDTOConfig(exclude={"login_count"}, partial=True)


class UserService(BaseUserService[User, Any]):  # type: ignore[type-var]
    async def post_login_hook(self, user: User, request: Request | None = None) -> None:
        # This will properly increment the user's `login_count`
        user.login_count += 1  # pyright: ignore


def example_authorization_guard(connection: "ASGIConnection", _: "BaseRouteHandler") -> None:
    """Authorize a request if the user's email string contains 'admin'."""
    if "admin" in connection.user.email:  # Don't do this in production
        return
    raise NotAuthorizedException()


sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=DATABASE_URL,
    session_dependency_key="session",
    session_config=AsyncSessionConfig(expire_on_commit=False),
)


async def on_startup() -> None:
    """Initialize the database."""
    async with sqlalchemy_config.get_engine().begin() as conn:  # pyright: ignore
        await conn.run_sync(UUIDBase.metadata.create_all)


litestar_users = LitestarUsersPlugin(
    config=LitestarUsersConfig(
        auth_backend_class=SessionAuth,
        session_backend_config=ServerSideSessionConfig(),
        secret=ENCODING_SECRET,
        user_model=User,  # pyright: ignore
        user_read_dto=UserReadDTO,
        user_registration_dto=UserRegistrationDTO,
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
    on_startup=[on_startup],
    plugins=[SQLAlchemyInitPlugin(config=sqlalchemy_config), litestar_users],
    route_handlers=[],
)

if __name__ == "__main__":
    uvicorn.run(app="basic:app", reload=True)
