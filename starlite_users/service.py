from typing import Generic, Dict, Any, Optional
from uuid import UUID

from starlite import ASGIConnection
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import UserNotFoundException
from .models import DatabaseModelType, User
from .repository import UserRepository
from .schema import CreateSchemaType, UpdateSchemaType

class UserService(Generic[DatabaseModelType, CreateSchemaType, UpdateSchemaType]):
    """Base class for services integrating to data persistence layers."""

    model_type: User

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def add(self, data: CreateSchemaType) -> User:
        return await self.repository.add(self.model_type(**data.dict(exclude_unset=True)))

    async def get(self, id_: UUID) -> User:
        return await self.repository.get(id_)

    async def update(self, id_: UUID, data: UpdateSchemaType) -> User:
        return await self.repository.update(self.model_type(**data.dict(exclude_unset=True), id=id_))

    async def delete(self, id_: UUID) -> None:
        return await self.repository.delete(id_)


def get_service(session: AsyncSession):
    """Instantiate service and repository for use with DI."""
    return UserService(UserRepository(session))
    

async def retrieve_user_handler(session: Dict[str, Any], connection: ASGIConnection) -> Optional[User]:
    async_session_maker = connection.app.state.session_maker_class

    async with async_session_maker() as async_session:
        async with async_session.begin():
            repository = UserRepository(async_session)
            try:
                return await repository.get(session.get('user_id', ''))
            except UserNotFoundException:
                return None
