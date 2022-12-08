from typing import Dict, Any, Optional, Type, Generic
from uuid import UUID

from starlite import ASGIConnection
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import UserNotFoundException
from .models import UserModelType
from .password import PasswordManager
from .repository import SQLAlchemyUserRepository
from .schema import UserCreateDTO, UserUpdateDTO, UserAuthSchema


class UserService(Generic[UserModelType]):
    """Base class for services integrating to data persistence layers."""

    model_type: Type[UserModelType]

    def __init__(self, repository: SQLAlchemyUserRepository) -> None:
        self.repository = repository
        self.password_manager = PasswordManager()
        self.model_type = repository.model_type

    async def add(self, data: UserCreateDTO) -> UserModelType:
        user_dict = data.dict(exclude={'password'}, exclude_unset=True)
        user_dict['password_hash'] = self.password_manager.get_hash(data.password)
        return await self.repository.add(self.model_type(**user_dict))

    async def get(self, id_: UUID) -> UserModelType:
        return await self.repository.get(id_)

    async def update(self, id_: UUID, data: UserUpdateDTO) -> UserModelType:
        return await self.repository.update(self.model_type(**data.dict(exclude_unset=True), id=id_))

    async def delete(self, id_: UUID) -> None:
        return await self.repository.delete(id_)

    async def authenticate(self, data: UserAuthSchema) -> Optional[UserModelType]:
        user = await self.repository.get_by(email=data.email)
        if user is None:
            return

        verified, new_password_hash = self.password_manager.verify_and_update(
            data.password, user.password_hash
        )
        if not verified:
            return
        if new_password_hash is not None:
            user.password_hash = new_password_hash
            await self.repository.update(user)

        return user


def get_service(session: AsyncSession, user_model: Type[UserModelType]):
    """Instantiate service and repository for use with DI."""
    return UserService(SQLAlchemyUserRepository(session=session, model_type=user_model))


def get_retrieve_user_handler(user_model: Type[UserModelType]):
    async def retrieve_user_handler(session: Dict[str, Any], connection: ASGIConnection) -> Optional[user_model]:
        async_session_maker = connection.app.state.session_maker_class

        async with async_session_maker() as async_session:
            async with async_session.begin():
                repository = SQLAlchemyUserRepository(session=async_session, model_type=user_model)
                try:
                    return await repository.get(session.get('user_id', ''))
                except UserNotFoundException:
                    return None
    return retrieve_user_handler
