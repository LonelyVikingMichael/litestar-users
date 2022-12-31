from typing import Any, Callable, Dict, Optional, Type

from starlite import ASGIConnection
from starlite.contrib.jwt import Token

from starlite_users.adapter.sqlalchemy.mixins import RoleModelType, UserModelType
from starlite_users.adapter.sqlalchemy.repository import SQLAlchemyUserRepository
from starlite_users.exceptions import RepositoryNotFoundException


def get_session_retrieve_user_handler(user_model: Type[UserModelType], role_model: Type[RoleModelType]) -> Callable:
    """Factory to get retrieve_user_handler functions for session backends.

    Args:
        user_model: A subclass of a `User` ORM model.
    """

    async def retrieve_user_handler(session: Dict[str, Any], connection: ASGIConnection) -> Optional[user_model]:
        """Handler to register with a Starlite auth backend, specific to SQLAlchemy.

        Args:
            session: Starlite session
        """
        async_session_maker = connection.app.state.session_maker_class

        async with async_session_maker() as async_session:
            async with async_session.begin():
                repository = SQLAlchemyUserRepository(
                    session=async_session, user_model_type=user_model, role_model_type=role_model
                )
                try:
                    user = await repository.get_user(session.get("user_id", ""))
                    if user.is_active and user.is_verified:
                        return user
                except RepositoryNotFoundException:
                    return None

    return retrieve_user_handler


def get_jwt_retrieve_user_handler(user_model: Type[UserModelType], role_model: Type[RoleModelType]) -> Callable:
    """Factory to get retrieve_user_handler functions for jwt backends.

    Args:
        user_model: A subclass of a `User` ORM model.
    """

    async def retrieve_user_handler(token: Token, connection: ASGIConnection[Any, Any, Any]) -> Optional[user_model]:
        """Handler to register with a Starlite auth backend, specific to SQLAlchemy.

        Args:
            token: Encoded JWT
        """
        async_session_maker = connection.app.state.session_maker_class

        async with async_session_maker() as async_session:
            async with async_session.begin():
                repository = SQLAlchemyUserRepository(
                    session=async_session, user_model_type=user_model, role_model_type=role_model
                )
                try:
                    user = await repository.get_user(token.sub)
                    if user.is_active and user.is_verified:
                        return user
                except RepositoryNotFoundException:
                    return None

    return retrieve_user_handler
