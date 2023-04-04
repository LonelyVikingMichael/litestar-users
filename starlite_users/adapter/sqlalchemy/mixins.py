from __future__ import annotations

from typing import TypeVar
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm.decl_api import declarative_mixin
from sqlalchemy.sql.sqltypes import Boolean, String, Uuid
from starlite.contrib.sqlalchemy.base import Base

__all__ = [
    "SQLAlchemyRoleMixin",
    "SQLAlchemyUserMixin",
    "UserModelType",
    "RoleModelType",
]


class SQLAlchemyUserMixin(Base):
    """Base SQLAlchemy user mixin."""

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)

    @property
    def roles(self) -> Mapped[list[SQLAlchemyRoleMixin]]:
        """Dummy placeholder."""
        return []


class SQLAlchemyRoleMixin(Base):
    """Base SQLAlchemy role mixin."""

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)


UserModelType = TypeVar("UserModelType", bound=SQLAlchemyUserMixin)
RoleModelType = TypeVar("RoleModelType", bound=SQLAlchemyRoleMixin)
