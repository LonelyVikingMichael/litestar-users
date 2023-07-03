from datetime import datetime
from typing import List, Optional

import uvicorn
from litestar import Litestar
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig, SQLAlchemyInitPlugin
from pydantic import SecretStr
from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import mapped_column, relationship

from starlite_users import StarliteUsers, StarliteUsersConfig
from starlite_users.adapter.sqlalchemy.mixins import SQLAlchemyRoleMixin, SQLAlchemyUserMixin
from starlite_users.config import (
    AuthHandlerConfig,
    CurrentUserHandlerConfig,
    PasswordResetHandlerConfig,
    RegisterHandlerConfig,
    RoleManagementHandlerConfig,
    UserManagementHandlerConfig,
    VerificationHandlerConfig,
)
from starlite_users.guards import roles_accepted, roles_required
from starlite_users.password import PasswordManager
from starlite_users.schema import (
    BaseRoleCreateDTO,
    BaseRoleReadDTO,
    BaseRoleUpdateDTO,
    BaseUserCreateDTO,
    BaseUserReadDTO,
    BaseUserUpdateDTO,
)
from starlite_users.service import BaseUserService

ENCODING_SECRET = "1234567890abcdef"  # noqa: S105
DATABASE_URL = "sqlite+aiosqlite:///"
password_manager = PasswordManager()


class User(UUIDBase, SQLAlchemyUserMixin):
    title = mapped_column(String(20))
    login_count = mapped_column(Integer(), default=0)

    roles = relationship("Role", secondary="user_role", lazy="joined")  # pyright: ignore


class Role(UUIDBase, SQLAlchemyRoleMixin):
    created_at = mapped_column(DateTime(), default=datetime.now)


class UserRole(UUIDBase):
    user_id = mapped_column(Uuid(), ForeignKey("user.id"))
    role_id = mapped_column(Uuid(), ForeignKey("role.id"))


class RoleCreateDTO(BaseRoleCreateDTO):
    pass


class RoleReadDTO(BaseRoleReadDTO):
    created_at: datetime


class RoleUpdateDTO(BaseRoleUpdateDTO):
    pass


class UserCreateDTO(BaseUserCreateDTO):
    title: str


class UserReadDTO(BaseUserReadDTO):
    title: str
    login_count: int
    # we need override `roles` to display our custom RoleDTO fields
    roles: List[Optional[RoleReadDTO]]


class UserUpdateDTO(BaseUserUpdateDTO):
    title: Optional[str]
    # we'll update `login_count` in the UserService.post_login_hook


class UserService(BaseUserService[User, UserCreateDTO, UserUpdateDTO, Role]):  # pyright: ignore
    async def post_login_hook(self, user: User) -> None:  # This will properly increment the user's `login_count`
        user.login_count += 1  # pyright: ignore


sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=DATABASE_URL,
    session_dependency_key="session",
)


async def on_startup() -> None:
    """Initialize the database."""
    async with sqlalchemy_config.create_engine().begin() as conn:  # pyright: ignore
        await conn.run_sync(UUIDBase.metadata.create_all)

    admin_role = Role(name="administrator", description="Top admin")
    admin_user = User(
        email="admin@example.com",
        password_hash=password_manager.hash(SecretStr("iamsuperadmin")),
        is_active=True,
        is_verified=True,
        title="Exemplar",
        roles=[admin_role],
    )
    session_maker = sqlalchemy_config.create_session_maker()
    async with session_maker() as session:
        async with session.begin():
            session.add(admin_user)


starlite_users = StarliteUsers(
    config=StarliteUsersConfig(
        auth_backend="session",
        secret=SecretStr("sixteenbits"),
        user_model=User,  # pyright: ignore
        user_read_dto=UserReadDTO,
        user_create_dto=UserCreateDTO,
        user_update_dto=UserUpdateDTO,
        role_model=Role,  # pyright: ignore
        role_create_dto=RoleCreateDTO,
        role_read_dto=RoleReadDTO,
        role_update_dto=RoleUpdateDTO,
        user_service_class=UserService,  # pyright: ignore
        auth_handler_config=AuthHandlerConfig(),
        current_user_handler_config=CurrentUserHandlerConfig(),
        password_reset_handler_config=PasswordResetHandlerConfig(),
        register_handler_config=RegisterHandlerConfig(),
        role_management_handler_config=RoleManagementHandlerConfig(guards=[roles_accepted("administrator")]),
        user_management_handler_config=UserManagementHandlerConfig(guards=[roles_required("administrator")]),
        verification_handler_config=VerificationHandlerConfig(),
    )
)

app = Litestar(
    debug=True,
    on_app_init=[starlite_users.on_app_init],
    on_startup=[on_startup],
    plugins=[SQLAlchemyInitPlugin(config=sqlalchemy_config)],
    route_handlers=[],
    openapi_config=openapi_config,
)

if __name__ == "__main__":
    uvicorn.run(app="with_roles:app", reload=True)
