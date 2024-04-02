from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID

from advanced_alchemy.exceptions import NotFoundError
from advanced_alchemy.extensions.litestar.plugins import SQLAlchemyAsyncConfig
from litestar.exceptions import ImproperlyConfiguredException
from sqlalchemy.orm import Load

from litestar_users.utils import get_litestar_users_plugin, get_sqlalchemy_plugin

__all__ = ["jwt_retrieve_user_handler", "session_retrieve_user_handler"]


if TYPE_CHECKING:
    from litestar.connection import ASGIConnection
    from litestar.contrib.jwt import Token
    from sqlalchemy import StatementLambdaElement

    from litestar_users.adapter.sqlalchemy.protocols import SQLAUserT
    from litestar_users.adapter.sqlalchemy.repository import SQLAlchemyUserRepository


def _get_user_repository(connection: ASGIConnection) -> SQLAlchemyUserRepository:
    sqlalchemy_config = get_sqlalchemy_plugin(connection.app)._config
    if not isinstance(sqlalchemy_config, SQLAlchemyAsyncConfig):
        raise ImproperlyConfiguredException("SQLAlchemy config must be of type `SQLAlchemyAsyncConfig`")
    async_session = sqlalchemy_config.provide_session(state=connection.app.state, scope=connection.scope)

    litestar_users_config = get_litestar_users_plugin(connection.app)._config
    return litestar_users_config.user_repository_class(
        session=async_session, model_type=litestar_users_config.user_model
    )


def _check_update_statement(connection: ASGIConnection, statement: StatementLambdaElement) -> StatementLambdaElement:
    if load_options := connection.route_handler.opt.get("user_load_options"):
        if not isinstance(load_options, Sequence):
            raise ValueError("user_load_options must be a sequence")
        if not all(isinstance(load_option, Load) for load_option in load_options):
            raise ValueError("all load options must be instances of `sqlalchemy.orm.Load`")
        return statement.options(*load_options)
    return statement


async def session_retrieve_user_handler(session: dict[str, Any], connection: ASGIConnection) -> SQLAUserT | None:
    """Get a user from the database based on session info.

    Args:
        session: Litestar session.
        connection: The ASGI connection.
    """
    repository = _get_user_repository(connection)
    try:
        # undocumented relationship loading api
        statement = _check_update_statement(connection, repository.statement)
        user_id = session.get("user_id")
        if user_id is None:
            return None
        user = await repository.get(UUID(user_id), statement=statement)
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
    repository = _get_user_repository(connection)
    try:
        # undocumented relationship loading api
        statement = _check_update_statement(connection, repository.statement)
        user_id: UUID | int | None = None
        try:
            user_id = UUID(token.sub)
        except ValueError:
            user_id = int(token.sub)
        user = await repository.get(user_id, statement=statement)
        if user.is_active and user.is_verified:
            return user  # type: ignore[no-any-return]
    except NotFoundError:
        pass
    return None
