from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession

from starlite_users.adapter.sqlalchemy.models import RoleModelType, UserModelType
from starlite_users.adapter.sqlalchemy.repository import SQLAlchemyUserRepository
from starlite_users.service import UserServiceType


def get_service_dependency(
    user_model: Type[UserModelType], role_model: Type[RoleModelType], user_service_class: Type[UserServiceType]
):
    """Factory to get service dependencies.

    Args:
        user_model: A subclass of a `User` ORM model.
        user_service_class: A subclass of [UserService][starlite_users.service.UserService]
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
