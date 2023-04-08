from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Sequence, cast

from litestar.contrib.sqlalchemy.init_plugin.config import GenericSQLAlchemyConfig
from litestar.exceptions import ImproperlyConfiguredException

from starlite_users.adapter.sqlalchemy.mixins import SQLAlchemyRoleMixin, SQLAlchemyUserMixin
from starlite_users.adapter.sqlalchemy.repository import SQLAlchemyRoleRepository

__all__ = ["get_service_dependency"]


if TYPE_CHECKING:
    from litestar.datastructures import State
    from litestar.types import Scope
    from pydantic import SecretStr
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from starlite_users.adapter.sqlalchemy.repository import SQLAlchemyUserRepository
    from starlite_users.service import UserServiceType


def get_service_dependency(
    user_model: type[SQLAlchemyUserMixin],
    user_service_class: type[UserServiceType],
    user_repository_class: type[SQLAlchemyUserRepository],
    role_model: type[SQLAlchemyRoleMixin] | None,
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
        try:
            session = cast("async_sessionmaker", state[GenericSQLAlchemyConfig.session_maker_app_state_key])
        except KeyError as err:
            raise ImproperlyConfiguredException("SQLAlchemyPlugin must be configured with SQLAlchemyConfig") from err

        user_repository = user_repository_class(session=session, user_model=user_model)
        role_repository = (
            None
            if role_model is None
            else SQLAlchemyRoleRepository[SQLAlchemyRoleMixin, SQLAlchemyUserMixin](
                session=session, role_model=role_model
            )
        )

        return user_service_class(
            user_repository=user_repository, role_repository=role_repository, secret=secret, hash_schemes=hash_schemes
        )

    return get_service
