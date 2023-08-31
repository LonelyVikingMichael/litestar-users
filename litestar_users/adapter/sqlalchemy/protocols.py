from __future__ import annotations

from uuid import UUID
from typing import Protocol, TypeVar, runtime_checkable

from litestar.contrib.sqlalchemy.base import ModelProtocol
from sqlalchemy.orm import MappedClassProtocol, Mapped


__all__ = ["SQLAlchemyRoleProtocol", "SQLAlchemyUserProtocol"]


SQLARoleT = TypeVar("SQLARoleT", bound="SQLAlchemyRoleProtocol")
SQLAUserT = TypeVar("SQLAUserT", bound="SQLAlchemyUserProtocol")


@runtime_checkable
class SQLAlchemyRoleProtocol(ModelProtocol, MappedClassProtocol, Protocol):  # pyright: ignore
    """The base SQLAlchemy role type."""

    id: Mapped[UUID]
    name: Mapped[str]
    description: Mapped[str]



@runtime_checkable
class SQLAlchemyUserProtocol(ModelProtocol, MappedClassProtocol, Protocol):  # pyright: ignore
    """The base SQLAlchemy user type."""

    id: Mapped[UUID]
    email: Mapped[str]
    password_hash: Mapped[str]
    is_active: Mapped[bool]
    is_verified: Mapped[bool]

    def __init__(*args: Any, **kwargs: Any) -> None:
        ...
