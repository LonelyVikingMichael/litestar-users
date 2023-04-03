from __future__ import annotations

from typing import TypeVar
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm.decl_api import declarative_mixin
from sqlalchemy.sql.sqltypes import Boolean, String, Uuid

__all__ = ["SQLAlchemyRoleMixin", "SQLAlchemyUserMixin"]


@declarative_mixin
class SQLAlchemyUserMixin:
    """Base SQLAlchemy user mixin."""

    id: Mapped[UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(1024))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)

    @property
    def roles(self) -> Mapped[list["SQLAlchemyRoleMixin"]]:
        """Dummy placeholder."""
        return []


@declarative_mixin
class SQLAlchemyRoleMixin:
    """Base SQLAlchemy role mixin."""

    id: Mapped[UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)


UserModelType = TypeVar("UserModelType", bound=SQLAlchemyUserMixin)
RoleModelType = TypeVar("RoleModelType", bound=SQLAlchemyRoleMixin)
