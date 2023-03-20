from __future__ import annotations

from typing import TypeVar
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm.attributes import Mapped  # type: ignore[attr-defined]  # noqa: TCH002
from sqlalchemy.orm.decl_api import declarative_mixin

from starlite_users.adapter.sqlalchemy.guid import GUID

__all__ = ["SQLAlchemyRoleMixin", "SQLAlchemyUserMixin"]


@declarative_mixin
class SQLAlchemyUserMixin:
    """Base SQLAlchemy user mixin."""

    id: Mapped[UUID] = Column(
        GUID(),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    email: Mapped[str] = Column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = Column(String(1024))
    is_active: Mapped[bool] = Column(Boolean(), nullable=False, default=False)
    is_verified: Mapped[bool] = Column(Boolean(), nullable=False, default=False)

    @property
    def roles(self) -> Mapped[list["SQLAlchemyRoleMixin"]]:
        """Dummy placeholder."""
        return []


@declarative_mixin
class SQLAlchemyRoleMixin:
    """Base SQLAlchemy role mixin."""

    id: Mapped[UUID] = Column(
        GUID(),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    name: Mapped[str] = Column(String(255), nullable=False, unique=True)
    description: Mapped[str] = Column(String(255), nullable=True)


UserModelType = TypeVar("UserModelType", bound=SQLAlchemyUserMixin)
RoleModelType = TypeVar("RoleModelType", bound=SQLAlchemyRoleMixin)
