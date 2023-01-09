from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Type

from starlite_users.adapter.sqlalchemy.mixins import SQLAlchemyUserRoleMixin
from starlite_users.adapter.sqlalchemy.repository import (
    SQLAlchemyUserRepository,
    SQLAlchemyUserRoleRepository,
)
from starlite_users.exceptions import RepositoryNotFoundException

if TYPE_CHECKING:
    from starlite import ASGIConnection
    from starlite.contrib.jwt import Token

    from starlite_users.adapter.sqlalchemy.mixins import RoleModelType, UserModelType


def get_session_retrieve_user_handler(
    user_model: "Type[UserModelType]", role_model: "Optional[Type[RoleModelType]]"
) -> Callable:
    """Get retrieve_user_handler functions for session backends.

    Args:
        user_model: A subclass of a `User` ORM model.
        role_model: A subclass of a `Role` ORM model.
    """

    async def retrieve_user_handler(
        session: Dict[str, Any], connection: "ASGIConnection[Any, Any, Any]"
    ) -> "Optional[UserModelType]":
        """Get a user from a session.

        Args:
            session: Starlite session.
            connection: The ASGI connection.
        """
        async_session_maker = connection.app.state.session_maker_class

        async with async_session_maker() as async_session:
            async with async_session.begin():
                if issubclass(user_model, SQLAlchemyUserRoleMixin) and role_model:
                    repository = SQLAlchemyUserRoleRepository(
                        session=async_session, user_model_type=user_model, role_model_type=role_model
                    )
                else:
                    repository = SQLAlchemyUserRepository(session=async_session, user_model_type=user_model)  # type: ignore[assignment]
                try:
                    user = await repository.get_user(session.get("user_id", ""))
                    if user.is_active and user.is_verified:
                        return user  # type: ignore[return-value]
                except RepositoryNotFoundException:
                    pass
        return None

    return retrieve_user_handler


def get_jwt_retrieve_user_handler(
    user_model: "Type[UserModelType]", role_model: "Optional[Type[RoleModelType]]"
) -> Callable:
    """Get retrieve_user_handler functions for jwt backends.

    Args:
        user_model: A subclass of a `User` ORM model.
        role_model: A subclass of a `Role` ORM model.
    """

    async def retrieve_user_handler(token: "Token", connection: "ASGIConnection[Any, Any, Any]") -> Optional[user_model]:  # type: ignore[valid-type]
        """Get a user from a JWT.

        Args:
            token: Encoded JWT.
            connection: The ASGI connection.
        """
        async_session_maker = connection.app.state.session_maker_class

        async with async_session_maker() as async_session:
            async with async_session.begin():
                if issubclass(user_model, SQLAlchemyUserRoleMixin) and role_model:
                    repository = SQLAlchemyUserRoleRepository(
                        session=async_session, user_model_type=user_model, role_model_type=role_model
                    )
                else:
                    repository = SQLAlchemyUserRepository(session=async_session, user_model_type=user_model)  # type: ignore[assignment]
                try:
                    user = await repository.get_user(token.sub)
                    if user.is_active and user.is_verified:
                        return user
                except RepositoryNotFoundException:
                    pass
        return None

    return retrieve_user_handler
