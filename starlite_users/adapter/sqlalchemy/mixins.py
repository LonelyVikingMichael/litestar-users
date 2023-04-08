from __future__ import annotations

from typing import TypeVar

from litestar.contrib.sqlalchemy.base import UUIDPrimaryKey
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column
from sqlalchemy.sql.sqltypes import Boolean, String

__all__ = [
    "SQLAlchemyRoleMixin",
    "SQLAlchemyUserMixin",
    "UserModelType",
    "RoleModelType",
]


@declarative_mixin
class SQLAlchemyUserMixin(UUIDPrimaryKey):
    """Base SQLAlchemy user mixin."""

    __abstract__ = True

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)

    @property
    def roles(self) -> Mapped[list[SQLAlchemyRoleMixin]]:
        """Dummy placeholder."""
        return []


@declarative_mixin
class SQLAlchemyRoleMixin(UUIDPrimaryKey):
    """Base SQLAlchemy role mixin."""

    __abstract__ = True

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)


UserModelType = TypeVar("UserModelType", bound=SQLAlchemyUserMixin)
RoleModelType = TypeVar("RoleModelType", bound=SQLAlchemyRoleMixin)
