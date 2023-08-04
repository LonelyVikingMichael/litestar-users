from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Generic

from litestar.contrib.jwt import Token
from litestar.contrib.repository.exceptions import NotFoundError
from litestar.contrib.repository.testing.generic_mock_repository import GenericAsyncMockRepository
from litestar.exceptions import NotAuthorizedException

from litestar_users.adapter.sqlalchemy.protocols import SQLARoleT, SQLAUserT

from .constants import ENCODING_SECRET

if TYPE_CHECKING:
    from uuid import UUID

    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler
    from litestar.testing import TestClient
    from sqlalchemy.ext.asyncio import AsyncSession

    from litestar_users import LitestarUsersConfig


def create_jwt(identifier: str) -> str:
    token = Token(exp=datetime.now() + timedelta(days=1), sub=identifier)
    return token.encode(secret=ENCODING_SECRET, algorithm="HS256")


class MockAuth:
    """Mock class to be used in authentication fixtures."""

    def __init__(self, client: "TestClient", config: "LitestarUsersConfig") -> None:
        self.client = client
        self.config = config

    def authenticate(self, user_id: "UUID") -> None:
        """Authenticate a TestClient request.

        Works with both session and JWT backends.
        """
        if self.config.auth_backend == "session":
            self.client.set_session_data({"user_id": user_id})
        elif self.config.auth_backend == "jwt" or self.config.auth_backend == "jwt_cookie":
            token = create_jwt(str(user_id))
            self.client.headers["Authorization"] = "Bearer " + token


class MockSQLAlchemyUserRepository(GenericAsyncMockRepository[SQLAUserT]):
    def __init__(self, session: AsyncSession, model_type: type[SQLAUserT]) -> None:
        self.model_type = model_type
        super().__init__(session=session)


class MockSQLAlchemyRoleRepository(GenericAsyncMockRepository[SQLARoleT], Generic[SQLARoleT, SQLAUserT]):
    def __init__(self, session: AsyncSession, model_type: type[SQLARoleT]) -> None:
        self.model_type = model_type
        super().__init__(session=session)

    async def get_role_by_name(self, name: str) -> SQLARoleT:
        for role in self.collection.values():
            if role.name == name:
                return role
        raise NotFoundError()

    async def assign_role(self, user: SQLAUserT, role: SQLARoleT) -> SQLAUserT:
        user.roles.append(role)  # pyright: ignore
        return user

    async def revoke_role(self, user: SQLAUserT, role: SQLARoleT) -> SQLAUserT:
        user.roles.remove(role)  # pyright: ignore
        return user


def basic_guard(connection: "ASGIConnection", _: "BaseRouteHandler") -> None:
    """Authorize a request if the user's email string contains 'admin'."""
    if "admin" in connection.user.email:
        return
    raise NotAuthorizedException()
