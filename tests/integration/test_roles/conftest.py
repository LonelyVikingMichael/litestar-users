from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import List
from uuid import UUID

import pytest
from litestar.contrib.sqlalchemy.base import UUIDBase
from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyAsyncConfig
from litestar.dto import DataclassDTO, DTOConfig
from litestar.middleware.session.server_side import (
    ServerSideSessionConfig,
)
from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, relationship

from litestar_users import LitestarUsersConfig
from litestar_users.adapter.sqlalchemy.mixins import (
    SQLAlchemyRoleMixin,
    SQLAlchemyUserMixin,
)
from litestar_users.config import RoleManagementHandlerConfig
from litestar_users.guards import roles_accepted, roles_required
from litestar_users.service import BaseUserService
from tests.conftest import password_manager
from tests.constants import ENCODING_SECRET

UUIDBase.metadata.clear()


class Role(UUIDBase, SQLAlchemyRoleMixin):
    pass


class User(UUIDBase, SQLAlchemyUserMixin):
    roles: Mapped[List[Role]] = relationship(Role, secondary="user_role", lazy="selectin")  # codespell: ignore type: ignore[misc]

class UserRole(UUIDBase):
    user_id = mapped_column(Uuid(), ForeignKey("user.id"))
    role_id = mapped_column(Uuid(), ForeignKey("role.id"))


class RoleReadDTO(SQLAlchemyDTO[Role]):
    """Role read DTO."""


class RoleCreateDTO(SQLAlchemyDTO[Role]):
    """Role creation DTO."""

    config = DTOConfig(exclude={"id"})


class RoleUpdateDTO(SQLAlchemyDTO[Role]):
    """Role update DTO."""

    config = DTOConfig(exclude={"id"}, partial=True)


@dataclass
class UserRegistrationSchema:
    email: str
    password: str
    title: str


class UserRegistrationDTO(DataclassDTO[UserRegistrationSchema]):
    """User registration DTO."""


class UserReadDTO(SQLAlchemyDTO[User]):
    config = DTOConfig(exclude={"password", "password_hash"})


class UserUpdateDTO(SQLAlchemyDTO[User]):
    """User update DTO."""

    config = DTOConfig(exclude={"id", "password", "password_hash", "roles"}, partial=True)


class UserService(BaseUserService[User, Role]):  # pyright: ignore
    pass


@pytest.fixture()
def admin_role() -> Role:
    return Role(
        id=UUID("9b62b52c-4278-4124-aca8-783ab281c196"),
        name="administrator",
        description="X",
    )


@pytest.fixture()
def writer_role() -> Role:
    return Role(
        id=UUID("76ddde3c-91d0-4b58-baa4-bfc4b3892ab2"),
        name="writer",
        description="He who writes",
    )


@pytest.fixture()
def admin_user(admin_role: Role) -> User:
    return User(
        id=UUID("01676112-d644-4f93-ab32-562850e89549"),
        email="admin@example.com",
        password_hash=password_manager.hash("iamsuperadmin"),
        is_active=True,
        is_verified=True,
        roles=[admin_role],
    )


@pytest.fixture()
def generic_user() -> User:
    return User(
        id=UUID("555d9ddb-7033-4819-a983-e817237b88e5"),
        email="good@example.com",
        password_hash=password_manager.hash("justauser"),
        is_active=True,
        is_verified=True,
        roles=[],
    )


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
        user_read_dto=UserReadDTO,
        user_registration_dto=UserRegistrationDTO,
        user_update_dto=UserUpdateDTO,
        role_model=Role,  # pyright: ignore
        user_service_class=UserService,
        role_management_handler_config=RoleManagementHandlerConfig(
            guards=[roles_accepted("administrator"), roles_required("administrator")]
        ),
    )


@pytest.fixture(autouse=True)
async def _seed_db(
    engine: AsyncEngine,
    sessionmaker: async_sessionmaker[AsyncSession],
    admin_user: User,
    generic_user: User,
    admin_role: Role,
    writer_role: Role,
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
        session.add_all([admin_user, generic_user, admin_role, writer_role])
        await session.commit()
    yield
