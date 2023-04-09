from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from litestar.contrib.jwt import Token
from litestar.contrib.repository.exceptions import NotFoundError
from litestar.contrib.repository.testing.generic_mock_repository import GenericMockRepository
from litestar.exceptions import NotAuthorizedException

from starlite_users.adapter.sqlalchemy.mixins import RoleModelType, UserModelType

from .constants import ENCODING_SECRET

if TYPE_CHECKING:
    from uuid import UUID

    from litestar.connection import ASGIConnection
    from litestar.handlers.base import BaseRouteHandler
    from litestar.testing import TestClient

    from starlite_users import StarliteUsersConfig


def create_jwt(identifier: str) -> str:
    token = Token(exp=datetime.now() + timedelta(days=1), sub=identifier)
    return token.encode(secret=ENCODING_SECRET.get_secret_value(), algorithm="HS256")


class MockAuth:
    """Mock class to be used in authentication fixtures."""

    def __init__(self, client: "TestClient", config: "StarliteUsersConfig") -> None:
        self.client = client
        self.config = config

    def authenticate(self, user_id: "UUID") -> None:
        """Authenticate a TestClient request.

        Works with both session and JWT backends.
        """
        if self.config.auth_backend == "session":
            self.client.set_session_data({"user_id": str(user_id)})
        elif self.config.auth_backend == "jwt" or self.config.auth_backend == "jwt_cookie":
            token = create_jwt(str(user_id))
            self.client.headers["Authorization"] = "Bearer " + token


class MockSQLAlchemyUserRepository(GenericMockRepository[UserModelType]):
    collection = {}


class MockSQLAlchemyRoleRepository(GenericMockRepository[RoleModelType]):
    collection = {}

    async def get_role_by_name(self, name: str) -> RoleModelType:
        for role in self.collection.values():
            if role.name == name:
                return role
        raise NotFoundError()

    async def assign_role_to_user(self, user: UserModelType, role: RoleModelType) -> UserModelType:
        user.roles.append(role)  # pyright: ignore
        return user

    async def revoke_role_from_user(self, user: UserModelType, role: RoleModelType) -> UserModelType:
        user.roles.remove(role)  # pyright: ignore
        return user


def basic_guard(connection: "ASGIConnection", _: "BaseRouteHandler") -> None:
    """Authorize a request if the user's email string contains 'admin'."""
    if "admin" in connection.user.email:
        return
    raise NotAuthorizedException()
