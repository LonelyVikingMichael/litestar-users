from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Sequence

from sqlalchemy.orm import Session
from starlite import State  # noqa: TCH002
from starlite.exceptions import ImproperlyConfiguredException
from starlite.plugins.sql_alchemy import SQLAlchemyPlugin
from starlite.types import Scope  # noqa: TCH002

__all__ = ["get_service_dependency"]


if TYPE_CHECKING:
    from pydantic import SecretStr

    from starlite_users.adapter.sqlalchemy.mixins import RoleModelType, UserModelType
    from starlite_users.adapter.sqlalchemy.repository import SQLAlchemyUserRepository
    from starlite_users.service import UserServiceType


def get_service_dependency(
    user_model: type["UserModelType"],
    user_service_class: type["UserServiceType"],
    user_repository_class: type[SQLAlchemyUserRepository],
    role_model: type[RoleModelType],
    secret: SecretStr,
    hash_schemes: Sequence[str] | None,
) -> Callable:
    """Get a service dependency callable.

    Args:
        user_model: A subclass of a `User` ORM model.
        role_model: A subclass of a `Role` ORM model.
        user_service_class: A subclass of [BaseUserService][starlite_users.service.BaseUserService]
        user_repository_class: A subclass of `BaseUserRepository` to use for database operations.
        secret: Secret string for securely signing tokens.
        hash_schemes: Schemes to use for password encryption.
    """

    def get_service(scope: Scope, state: State) -> UserServiceType:
        """Instantiate service and repository for use with DI.

        Args:
            scope: ASGI scope
            state: The application.state instance
        """
        session = None
        if not any(isinstance(plugin, SQLAlchemyPlugin) for plugin in scope["app"].plugins):
            raise ImproperlyConfiguredException("SQLAlchemyPlugin must be configured with SQLAlchemyConfig")
        for plugin in scope["app"].plugins:
            if isinstance(plugin, SQLAlchemyPlugin):
                if plugin._config is None:
                    raise ImproperlyConfiguredException("SQLAlchemyPlugin must be configured with SQLAlchemyConfig")
                session = plugin._config.create_db_session_dependency(state, scope)
                break

        if session is None or isinstance(session, Session):
            raise ImproperlyConfiguredException("session must be instance of sqlalchemy.AsyncSession")

        repository = user_repository_class(session=session, user_model=user_model, role_model=role_model)

        return user_service_class(repository=repository, secret=secret, hash_schemes=hash_schemes)

    return get_service
