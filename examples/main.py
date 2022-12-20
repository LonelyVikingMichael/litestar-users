from uuid import uuid4

import uvicorn
from pydantic import SecretStr
from sqlalchemy import Column
from sqlalchemy.orm import declarative_base
from starlite import Starlite
from starlite.middleware.session.memory_backend import MemoryBackendConfig
from starlite.plugins.sql_alchemy import SQLAlchemyConfig, SQLAlchemyPlugin

from starlite_users import StarliteUsersConfig, StarliteUsersPlugin
from starlite_users.adapter.sqlalchemy.guid import GUID
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
from starlite_users.password import PasswordManager
from starlite_users.schema import UserReadDTO, UserUpdateDTO
from starlite_users.service import UserService

ENCODING_SECRET = "1234567890abcdef"
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


class User(Base, SQLAlchemyUserModel):
    pass  # add custom attributes


class Role(Base, SQLAlchemyRoleModel):
    pass


class UserRole(Base, UserRoleAssociation):
    pass


class MyUserReadDTO(UserReadDTO):
    pass  # add custom attributes


class MyUserUpdateDTO(UserUpdateDTO):
    pass  # add custom attributes


class MyUserService(UserService):
    user_model = User
    secret = SecretStr(ENCODING_SECRET)


sqlalchemy_config = SQLAlchemyConfig(
    connection_string=DATABASE_URL,
    dependency_key="session",
)


async def on_startup() -> None:
    """Initialize the database."""
    async with sqlalchemy_config.engine.begin() as conn:  # type: ignore
        await conn.run_sync(Base.metadata.create_all)

    admin_role = Role(name="administrator", description="Top admin")
    admin_user = User(
        email="admin@example.com",
        password_hash=password_manager.get_hash(SecretStr("iamsuperadmin")),
        is_active=True,
        is_verified=True,
        roles=[admin_role],
    )

    async with sqlalchemy_config.session_maker() as session:
        async with session.begin():
            session.add_all([admin_role, admin_user])


starlite_users = StarliteUsersPlugin(
    config=StarliteUsersConfig(
        auth_backend="session",
        secret=ENCODING_SECRET,
        session_backend_config=MemoryBackendConfig(),
        user_model=User,
        role_model=Role,
        user_read_dto=MyUserReadDTO,
        user_update_dto=MyUserUpdateDTO,
        user_service_class=MyUserService,
        auth_handler_config=AuthHandlerConfig(),
        current_user_handler_config=CurrentUserHandlerConfig(),
        password_reset_handler_config=PasswordResetHandlerConfig(),
        register_handler_config=RegisterHandlerConfig(),
        user_management_handler_config=UserManagementHandlerConfig(),
        verification_handler_config=VerificationHandlerConfig(),
    )
)

app = Starlite(
    debug=True,
    on_app_init=[starlite_users.on_app_init],
    on_startup=[on_startup],
    plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
    route_handlers=[],
)

if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True)
