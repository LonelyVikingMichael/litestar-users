from typing import Any, Dict, Optional, Generic, Type
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound, IntegrityError

from .exceptions import UserNotFoundException, UserConflictException
from .models import UserModelType


class SQLAlchemyUserRepository(Generic[UserModelType]):  # TODO: create generic base for picolo, tortoise etc
    """SQLAlchemy implementation of user persistence layer."""

    model_type: Type[UserModelType]

    def __init__(self, session: AsyncSession, model_type: Type[UserModelType]) -> None:
        self.session = session
        self.model_type = model_type

    async def add(self, user: UserModelType) -> UserModelType:
        try:
            self.session.add(user)
            await self.session.flush()
            await self.session.refresh(user)

            return user
        except IntegrityError as e:
            raise UserConflictException from e

    async def get(self, id_: UUID) -> UserModelType:
        result = await self.session.execute(select(self.model_type).where(self.model_type.id == id_))
        try:
            return result.unique().scalar_one()
        except NoResultFound as e:
            raise UserNotFoundException from e

    async def get_by(self, **kwargs: Any) -> Optional[UserModelType]:
        result = await self.session.execute(
            select(self.model_type).where(*(getattr(self.model_type, k) == v for k, v in kwargs.items()))
        )
        return result.unique().scalar_one()

    async def update(self, id_: UUID, data: Dict[str, Any]) -> UserModelType:
        user = await self.get(id_)
        return await self._update(user, data)

    async def delete(self, id_: UUID) -> None:
        record = await self.get(id_)
        await self.session.delete(record)

    async def _update(self, user: UserModelType, data: Dict[str, Any]) -> UserModelType:
        for attr, val in data.items():
            setattr(user, attr, val)
