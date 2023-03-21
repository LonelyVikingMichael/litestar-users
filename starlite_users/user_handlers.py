from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from starlite_users.exceptions import RepositoryNotFoundException

__all__ = ["get_jwt_retrieve_user_handler", "get_session_retrieve_user_handler"]


if TYPE_CHECKING:
    from starlite import ASGIConnection
    from starlite.contrib.jwt import Token

    from starlite_users.adapter.sqlalchemy.mixins import RoleModelType, UserModelType
    from starlite_users.generics import AbstractUserRepository


def get_session_retrieve_user_handler(
    user_model: type[UserModelType],
    role_model: type[RoleModelType],
    user_repository_class: type[AbstractUserRepository],
) -> Callable:
    """Get retrieve_user_handler functions for session backends.

    Args:
        user_model: A subclass of a `User` ORM model.
        role_model: A subclass of a `Role` ORM model.
        user_repository_class: A subclass of `BaseUserRepository` to use for database operations.
    """

    async def retrieve_user_handler(
        session: dict[str, Any], connection: ASGIConnection[Any, Any, Any]
    ) -> UserModelType | None:
        """Get a user from the database based on session info.

        Args:
            session: Starlite session.
            connection: The ASGI connection.
        """
        async_session_maker = connection.app.state.session_maker_class

        async with async_session_maker() as async_session:
            async with async_session.begin():
                repository = user_repository_class(session=async_session, user_model=user_model, role_model=role_model)
                try:
                    user = await repository.get_user(session.get("user_id", ""))
                    if user.is_active and user.is_verified:
                        return user  # type: ignore[no-any-return]
                except RepositoryNotFoundException:
                    pass
        return None

    return retrieve_user_handler


def get_jwt_retrieve_user_handler(
    user_model: type[UserModelType],
    role_model: type[RoleModelType],
    user_repository_class: type[AbstractUserRepository],
) -> Callable:
    """Get retrieve_user_handler functions for jwt backends.

    Args:
        user_model: A subclass of a `User` ORM model.
        role_model: A subclass of a `Role` ORM model.
        user_repository_class: A subclass of `BaseUserRepository` to use for database operations.
    """

    async def retrieve_user_handler(token: Token, connection: ASGIConnection[Any, Any, Any]) -> user_model | None:  # type: ignore[valid-type]
        """Get a user from the database based on JWT info.

        Args:
            token: Encoded JWT.
            connection: The ASGI connection.
        """
        async_session_maker = connection.app.state.session_maker_class

        async with async_session_maker() as async_session:
            async with async_session.begin():
                repository = user_repository_class(session=async_session, user_model=user_model, role_model=role_model)
                try:
                    user = await repository.get_user(token.sub)
                    if user.is_active and user.is_verified:
                        return user  # type: ignore[no-any-return]
                except RepositoryNotFoundException:
                    pass
        return None

    return retrieve_user_handler
