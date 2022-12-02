from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from .exceptions import UserNotFoundException
from .models import User

class UserRepository:
    """User persistence layer."""

    model_type: User

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def get(self, id_: UUID) -> User:
        result = await self.session.execute(select(self.model_type).where(self.model_type.id == id_))
        try:
            return result.scalar_one()
        except NoResultFound as e:
            raise UserNotFoundException from e

    async def update(self, data: User) -> User:
        await self.get(data.id)
        return await self.session.merge(data)

    async def delete(self, id_: UUID) -> None:
        record = await self.get(id_)
        await self.session.delete(record)
