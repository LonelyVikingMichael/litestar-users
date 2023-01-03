from typing import Callable, Type, cast

from sqlalchemy.orm import sessionmaker
from starlite import State
from starlite.plugins.sql_alchemy import SQLAlchemyPlugin
from starlite.plugins.sql_alchemy.config import SESSION_SCOPE_KEY
from starlite.types import Scope

from starlite_users.adapter.sqlalchemy.mixins import RoleModelType, UserModelType
from starlite_users.adapter.sqlalchemy.repository import SQLAlchemyUserRepository
from starlite_users.service import UserServiceType


def get_service_dependency(
    user_model: Type[UserModelType], role_model: Type[RoleModelType], user_service_class: Type[UserServiceType]
) -> Callable:
    """Factory to get service dependencies.

    Args:
        user_model: A subclass of a `User` ORM model.
        user_service_class: A subclass of [BaseUserService][starlite_users.service.BaseUserService]
    """

    def get_service(scope: Scope, state: State) -> UserServiceType:
        """Instantiate service and repository for use with DI.

        Args:
            scope: ASGI scope
            state: The application.state instance
        """
        for plugin in scope["app"].plugins:
            if isinstance(plugin, SQLAlchemyPlugin):
                session = plugin._config.create_db_session_dependency(state, scope)
                break

        return user_service_class(
            SQLAlchemyUserRepository(session=session, user_model_type=user_model, role_model_type=role_model)
        )

    return get_service
