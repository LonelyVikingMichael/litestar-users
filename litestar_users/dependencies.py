from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from litestar_users.adapter.sqlalchemy.repository import SQLAlchemyRoleRepository
from litestar_users.config import LitestarUsersConfig

__all__ = ["provide_user_service"]


if TYPE_CHECKING:
    from litestar.datastructures import State
    from litestar.types import Scope

    from litestar_users.service import BaseUserService


def provide_user_service(scope: Scope, state: State) -> BaseUserService[Any, Any]:
    """Instantiate service and repository for use with DI.

    Args:
        scope: ASGI scope
        state: The application.state instance
    """
    config = cast(LitestarUsersConfig, state.litestar_users_config)
    session = config.sqlalchemy_plugin_config.provide_session(state=state, scope=scope)

    user_repository = config.user_repository_class(session=session, model_type=config.user_model)
    role_repository: SQLAlchemyRoleRepository | None = (
        None if config.role_model is None else SQLAlchemyRoleRepository(session=session, model_type=config.role_model)
    )

    return config.user_service_class(
        user_repository=user_repository,
        role_repository=role_repository,
        secret=config.secret,
        hash_schemes=config.hash_schemes,
    )
