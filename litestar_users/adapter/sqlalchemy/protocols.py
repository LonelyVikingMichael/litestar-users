from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from litestar.contrib.sqlalchemy.base import ModelProtocol
from sqlalchemy.orm import MappedClassProtocol

from litestar_users.protocols import RoleModelProtocol, UserModelProtocol

__all__ = ["SQLAlchemyRoleProtocol", "SQLAlchemyUserProtocol"]


SQLARoleT = TypeVar("SQLARoleT", bound="SQLAlchemyRoleProtocol")
SQLAUserT = TypeVar("SQLAUserT", bound="SQLAlchemyUserProtocol")


@runtime_checkable
class SQLAlchemyRoleProtocol(ModelProtocol, RoleModelProtocol, MappedClassProtocol, Protocol):  # pyright: ignore
    """The base SQLAlchemy role type."""


@runtime_checkable
class SQLAlchemyUserProtocol(ModelProtocol, UserModelProtocol, MappedClassProtocol, Protocol):  # pyright: ignore
    """The base SQLAlchemy user type."""
