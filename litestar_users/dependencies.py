from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Sequence

from litestar_users.adapter.sqlalchemy.repository import SQLAlchemyRoleRepository

__all__ = ["get_service_dependency"]


if TYPE_CHECKING:
    from advanced_alchemy.extensions.litestar.plugins import SQLAlchemyAsyncConfig
    from litestar.datastructures import State
    from litestar.types import Scope

    from litestar_users.adapter.sqlalchemy.protocols import SQLARoleT, SQLAUserT
    from litestar_users.adapter.sqlalchemy.repository import SQLAlchemyUserRepository
    from litestar_users.service import UserServiceType


def get_service_dependency(
    user_model: type[SQLAUserT],
    user_service_class: type[UserServiceType],
    user_repository_class: type[SQLAlchemyUserRepository[SQLAUserT]],
    role_model: type[SQLARoleT] | None,
    secret: str,
    sqlalchemy_plugin_config: SQLAlchemyAsyncConfig,
    hash_schemes: Sequence[str] | None,
) -> Callable:
    """Get a service dependency callable.

    Args:
        user_model: A subclass of a `User` ORM model.
        role_model: A subclass of a `Role` ORM model.
        user_service_class: A subclass of [BaseUserService][litestar_users.service.BaseUserService]
        user_repository_class: A subclass of `BaseUserRepository` to use for database operations.
        secret: Secret string for securely signing tokens.
        sqlalchemy_plugin_config: The Litestar SQLAlchemy plugin config instance.
        hash_schemes: Schemes to use for password encryption.
    """

    def get_service(scope: Scope, state: State) -> UserServiceType:
        """Instantiate service and repository for use with DI.

        Args:
            scope: ASGI scope
            state: The application.state instance
        """

        session = sqlalchemy_plugin_config.provide_session(state=state, scope=scope)

        user_repository = user_repository_class(session=session, model_type=user_model)
        role_repository: SQLAlchemyRoleRepository | None = (
            None if role_model is None else SQLAlchemyRoleRepository(session=session, model_type=role_model)
        )

        return user_service_class(
            user_repository=user_repository, role_repository=role_repository, secret=secret, hash_schemes=hash_schemes
        )

    return get_service
