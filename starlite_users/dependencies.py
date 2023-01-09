from typing import TYPE_CHECKING, Callable, Optional, Type

from sqlalchemy.orm import Session
from starlite import State  # noqa: TC002
from starlite.exceptions import ImproperlyConfiguredException
from starlite.plugins.sql_alchemy import SQLAlchemyPlugin
from starlite.types import Scope  # noqa: TC002

from starlite_users.adapter.sqlalchemy.mixins import SQLAlchemyUserRoleMixin
from starlite_users.adapter.sqlalchemy.repository import (
    SQLAlchemyUserRepository,
    SQLAlchemyUserRoleRepository,
)

if TYPE_CHECKING:
    from starlite_users.adapter.sqlalchemy.mixins import RoleModelType, UserModelType
    from starlite_users.service import UserServiceType


def get_service_dependency(
    user_model: Type["UserModelType"],
    role_model: Optional[Type["RoleModelType"]],
    user_service_class: Type["UserServiceType"],
) -> Callable:
    """Get a service dependency callable.

    Args:
        user_model: A subclass of a `User` ORM model.
        role_model: A subclass of a `Role` ORM model.
        user_service_class: A subclass of [BaseUserService][starlite_users.service.BaseUserService]
    """

    def get_service(scope: "Scope", state: "State") -> "UserServiceType":
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

        if issubclass(user_model, SQLAlchemyUserRoleMixin) and role_model:
            repository = SQLAlchemyUserRoleRepository(
                session=session, user_model_type=user_model, role_model_type=role_model
            )
        else:
            repository = SQLAlchemyUserRepository(session=session, user_model_type=user_model)  # type: ignore[assignment]

        return user_service_class(repository)

    return get_service
