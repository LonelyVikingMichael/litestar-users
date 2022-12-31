from typing import Callable, Type

from sqlalchemy.ext.asyncio import AsyncSession

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

    def get_service(session: AsyncSession) -> UserServiceType:
        """Instantiate service and repository for use with DI.

        Args:
            session: SQLAlchemy AsyncSession
        """
        return user_service_class(
            SQLAlchemyUserRepository(session=session, user_model_type=user_model, role_model_type=role_model)
        )

    return get_service
