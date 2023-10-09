from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable
from uuid import UUID

from litestar.repository.exceptions import NotFoundError

__all__ = ["get_jwt_retrieve_user_handler", "get_session_retrieve_user_handler"]


if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar.plugins import SQLAlchemyAsyncConfig
    from litestar.connection import ASGIConnection
    from litestar.contrib.jwt import Token

    from litestar_users.adapter.sqlalchemy.protocols import SQLAUserT
    from litestar_users.adapter.sqlalchemy.repository import SQLAlchemyUserRepository


def get_session_retrieve_user_handler(
    user_model: type[SQLAUserT],
    user_repository_class: type[SQLAlchemyUserRepository[SQLAUserT]],
    sqlalchemy_plugin_config: SQLAlchemyAsyncConfig,
) -> Callable:
    """Get retrieve_user_handler functions for session backends.

    Args:
        user_model: A subclass of a `User` ORM model.
        user_repository_class: A subclass of `BaseUserRepository` to use for database operations.
        sqlalchemy_plugin_config: The Litestar SQLAlchemy plugin config instance.
    """

    async def retrieve_user_handler(session: dict[str, Any], connection: ASGIConnection) -> SQLAUserT | None:
        """Get a user from the database based on session info.

        Args:
            session: Litestar session.
            connection: The ASGI connection.
        """

        async_session = sqlalchemy_plugin_config.provide_session(state=connection.app.state, scope=connection.scope)
        repository = user_repository_class(session=async_session, model_type=user_model)
        try:
            user_id = session.get("user_id", "")
            user = await repository.get(UUID(user_id))
            if user.is_active and user.is_verified:
                return user
        except NotFoundError:
            pass
        return None

    return retrieve_user_handler


def get_jwt_retrieve_user_handler(
    user_model: type[SQLAUserT],
    user_repository_class: type[SQLAlchemyUserRepository],
    sqlalchemy_plugin_config: SQLAlchemyAsyncConfig,
) -> Callable:
    """Get retrieve_user_handler functions for jwt backends.

    Args:
        user_model: A subclass of a `User` ORM model.
        user_repository_class: A subclass of `BaseUserRepository` to use for database operations.
        sqlalchemy_plugin_config: The Litestar SQLAlchemy plugin config instance.
    """

    async def retrieve_user_handler(token: Token, connection: ASGIConnection) -> user_model | None:  # type: ignore[valid-type]
        """Get a user from the database based on JWT info.

        Args:
            token: Encoded JWT.
            connection: The ASGI connection.
        """

        async_session = sqlalchemy_plugin_config.provide_session(state=connection.app.state, scope=connection.scope)
        repository = user_repository_class(session=async_session, model_type=user_model)
        try:
            user = await repository.get(UUID(token.sub))
            if user.is_active and user.is_verified:
                return user  # type: ignore[no-any-return]
        except NotFoundError:
            pass
        return None

    return retrieve_user_handler
