from typing import Dict, Any, Optional
from uuid import UUID

from starlite import ASGIConnection
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import UserNotFoundException
from .models import User
from .password import PasswordManager
from .repository import SQLAlchemyUserRepository
from .schema import UserCreateDTO, UserUpdateDTO, UserAuthSchema


class UserService:
    """Base class for services integrating to data persistence layers."""

    model_type: User

    def __init__(self, repository: SQLAlchemyUserRepository) -> None:
        self.repository = repository
        self.password_manager = PasswordManager()

    async def add(self, data: UserCreateDTO) -> User:
        user_dict = data.dict(exclude={'password'}, exclude_unset=True)
        user_dict['password_hash'] = self.password_manager.get_hash(data.password)
        return await self.repository.add(User(**user_dict))

    async def get(self, id_: UUID) -> User:
        return await self.repository.get(id_)

    async def update(self, id_: UUID, data: UserUpdateDTO) -> User:
        return await self.repository.update(User(**data.dict(exclude_unset=True), id=id_))

    async def delete(self, id_: UUID) -> None:
        return await self.repository.delete(id_)

    async def authenticate(self, data: UserAuthSchema) -> Optional[User]:
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


def get_service(session: AsyncSession):
    """Instantiate service and repository for use with DI."""
    return UserService(SQLAlchemyUserRepository(session))


async def retrieve_user_handler(session: Dict[str, Any], connection: ASGIConnection) -> Optional[User]:
    async_session_maker = connection.app.state.session_maker_class

    async with async_session_maker() as async_session:
        async with async_session.begin():
            repository = SQLAlchemyUserRepository(async_session)
            try:
                return await repository.get(session.get('user_id', ''))
            except UserNotFoundException:
                return None
