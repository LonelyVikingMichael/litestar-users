from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.extensions.litestar.plugins import SQLAlchemyAsyncConfig
from litestar.exceptions import ImproperlyConfiguredException

from litestar_users.utils import get_litestar_users_plugin, get_sqlalchemy_plugin

__all__ = ["jwt_retrieve_user_handler", "session_retrieve_user_handler"]


if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.contrib.jwt import Token

    from litestar_users.adapter.sqlalchemy.protocols import SQLAUserT


async def session_retrieve_user_handler(session: dict[str, Any], connection: ASGIConnection) -> SQLAUserT | None:
    """Get a user from the database based on session info.

    Args:
        session: Litestar session.
        connection: The ASGI connection.
    """

    sqlalchemy_config = get_sqlalchemy_plugin(connection.app)._config
    if not isinstance(sqlalchemy_config, SQLAlchemyAsyncConfig):
        raise ImproperlyConfiguredException("SQLAlchemy config must be of type `SQLAlchemyAsyncConfig`")
    async_session = sqlalchemy_config.provide_session(state=connection.app.state, scope=connection.scope)

    litestar_users_config = get_litestar_users_plugin(connection.app)._config
    repository = litestar_users_config.user_repository_class(
        session=async_session, model_type=litestar_users_config.user_model
    )
    try:
        user_id = session.get("user_id")
        if user_id is None:
            return None
        user = await repository.get(UUID(user_id))
        if user.is_active and user.is_verified:
            return user  # type: ignore[no-any-return]
    except NotFoundError:
        pass
    return None


async def jwt_retrieve_user_handler(token: Token, connection: ASGIConnection) -> SQLAUserT | None:
    """Get a user from the database based on JWT info.

    Args:
        token: Encoded JWT.
        connection: The ASGI connection.
    """

    sqlalchemy_config = get_sqlalchemy_plugin(connection.app)._config
    if not isinstance(sqlalchemy_config, SQLAlchemyAsyncConfig):
        raise ImproperlyConfiguredException("SQLAlchemy config must be of type `SQLAlchemyAsyncConfig`")
    async_session = sqlalchemy_config.provide_session(state=connection.app.state, scope=connection.scope)

    litestar_users_config = get_litestar_users_plugin(connection.app)._config
    repository = litestar_users_config.user_repository_class(
        session=async_session, model_type=litestar_users_config.user_model
    )
    try:
        user = await repository.get(UUID(token.sub))
        if user.is_active and user.is_verified:
            return user  # type: ignore[no-any-return]
    except NotFoundError:
        pass
    return None
