from __future__ import annotations

from typing import TypeVar

from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column
from sqlalchemy.sql.sqltypes import Boolean, String

__all__ = [
    "SQLAlchemyRoleMixin",
    "SQLAlchemyUserMixin",
    "UserModelType",
    "RoleModelType",
]


@declarative_mixin
class SQLAlchemyUserMixin:
    """Base SQLAlchemy user mixin."""

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)


@declarative_mixin
class SQLAlchemyRoleMixin:
    """Base SQLAlchemy role mixin."""

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)


UserModelType = TypeVar("UserModelType", bound=SQLAlchemyUserMixin)
RoleModelType = TypeVar("RoleModelType", bound=SQLAlchemyRoleMixin)
