from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, Type
from uuid import uuid4

from starlite import NotAuthorizedException
from starlite.contrib.jwt import Token
from starlite.exceptions import ImproperlyConfiguredException

from starlite_users.adapter.sqlalchemy.mixins import RoleModelType, UserModelType
from starlite_users.adapter.sqlalchemy.repository import SQLAlchemyUserRepository
from starlite_users.exceptions import RepositoryNotFoundException

from .constants import ENCODING_SECRET

if TYPE_CHECKING:
    from uuid import UUID

    from starlite import ASGIConnection, BaseRouteHandler
    from starlite.testing import TestClient

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


class MockSQLAlchemyUserRepository(SQLAlchemyUserRepository[UserModelType, RoleModelType]):
    user_store: Dict[str, UserModelType] = {}
    role_store: Dict[str, RoleModelType] = {}

    def __init__(
        self, user_model: Type[UserModelType], role_model: Type[RoleModelType], *args: Any, **kwargs: Any
    ) -> None:
        self.user_model = user_model
        self.role_model = role_model

    async def add_user(self, data: UserModelType) -> UserModelType:
        data.id = str(uuid4())
        self.user_store[data.id] = data
        return data

    async def get_user(self, id_: "UUID") -> UserModelType:
        result = self.user_store.get(str(id_))
        if result is None:
            raise RepositoryNotFoundException()
        return result

    async def get_user_by(self, **kwargs: Any) -> UserModelType:
        for user in self.user_store.values():
            if all(getattr(user, key) == kwargs[key] for key in kwargs.keys()):
                return user
        raise RepositoryNotFoundException()

    async def update_user(self, id_: "UUID", data: Dict[str, Any]) -> UserModelType:
        result = await self.get_user(id_)
        for k, v in data.items():
            setattr(result, k, v)
        return result

    async def delete_user(self, id_: "UUID") -> None:
        self.user_store.pop(str(id_))

    async def add_role(self, data: RoleModelType) -> RoleModelType:
        if data is None:
            raise ImproperlyConfiguredException("StarliteUsersConfig.role_model must subclass SQLAlchemyRoleMixin")
        data.id = str(uuid4())
        self.role_store[data.id] = data
        return data

    async def get_role(self, id_: "UUID") -> RoleModelType:
        result = self.role_store.get(str(id_))
        if result is None:
            raise RepositoryNotFoundException()
        return result

    async def get_role_by_name(self, name: str) -> RoleModelType:
        for role in self.role_store.values():
            if role.name == name:
                return role
        raise RepositoryNotFoundException()

    async def update_role(self, id_: "UUID", data: Dict[str, Any]) -> RoleModelType:
        result = await self.get_role(id_)
        for k, v in data.items():
            setattr(result, k, v)
        return result

    async def delete_role(self, id_: "UUID") -> None:
        self.role_store.pop(str(id_))

    async def assign_role_to_user(self, user: UserModelType, role: RoleModelType) -> UserModelType:
        user.roles.append(role)
        return user

    async def revoke_role_from_user(self, user: UserModelType, role: RoleModelType) -> UserModelType:
        user.roles.remove(role)
        return user


def basic_guard(connection: "ASGIConnection", _: "BaseRouteHandler") -> None:
    """Authorize a request if the user's email string contains 'admin'."""

    if "admin" in connection.user.email:
        return
    raise NotAuthorizedException()
