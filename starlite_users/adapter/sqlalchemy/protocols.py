from __future__ import annotations

from typing import TypeVar

from litestar.contrib.sqlalchemy.base import ModelProtocol

from starlite_users.protocols import RoleModelProtocol, UserModelProtocol

__all__ = ["SQLAlchemyRoleProtocol", "SQLAlchemyUserProtocol"]


SQLARoleT = TypeVar("SQLARoleT", bound="SQLAlchemyRoleProtocol")
SQLAUserT = TypeVar("SQLAUserT", bound="SQLAlchemyUserProtocol")


class SQLAlchemyRoleProtocol(ModelProtocol, RoleModelProtocol):
    """The base SQLAlchemy role type."""


class SQLAlchemyUserProtocol(ModelProtocol, UserModelProtocol):
    """The base SQLAlchemy user type."""
