from typing import Any, Dict, Generic, Optional, Type
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from ...exceptions import UserConflictException, UserNotFoundException
from .models import UserModelType


class SQLAlchemyUserRepository(Generic[UserModelType]):  # TODO: create generic base for picolo, tortoise etc
    """SQLAlchemy implementation of user persistence layer."""

    model_type: Type[UserModelType]

    def __init__(self, session: AsyncSession, model_type: Type[UserModelType]) -> None:
        """Initialise a repository instance.

        Args:
            session: A SQLAlchemy `AsyncSession`.
            model_type: A subclass of [SQLAlchemyUser][starlite_users.models.SQLAlchemyUser]
        """
        self.session = session
        self.model_type = model_type

    async def add(self, user: UserModelType) -> UserModelType:
        """Add a user to the database.

        Args:
            user: A SQLAlchemy User model.
        """
        try:
            self.session.add(user)
            await self.session.flush()
            await self.session.refresh(user)

            await self.session.commit()

            return user
        except IntegrityError as e:
            raise UserConflictException from e

    async def get(self, id_: UUID) -> UserModelType:
        """Retrieve a user from the database by id.

        Args:
            id_: UUID corresponding to a user primary key.

        Raises:
            UserNotFoundException: when no user matches the query.
        """
        result = await self.session.execute(select(self.model_type).where(self.model_type.id == id_))
        try:
            return result.unique().scalar_one()
        except NoResultFound as e:
            raise UserNotFoundException from e

    async def get_by(self, **kwargs: Any) -> Optional[UserModelType]:
        """Retrieve a user from the database by arbitrary keyword arguments.

        Args:
            **kwargs: Keyword arguments to pass as filters.

        Examples:
            ```python
            repository = SQLAlchemyUserRepository(...)
            john = await repository.get_by(email='john@example.com')
            ```

        Raises:
            UserNotFoundException: when no user matches the query.
        """
        result = await self.session.execute(
            select(self.model_type).where(*(getattr(self.model_type, k) == v for k, v in kwargs.items()))
        )
        try:
            return result.unique().scalar_one()
        except NoResultFound as e:
            raise UserNotFoundException from e

    async def update(self, id_: UUID, data: Dict[str, Any]) -> UserModelType:
        """Update arbitrary user attributes in the database.

        Args:
            id_: UUID corresponding to a user primary key.
            data: Dictionary to map to user columns and values.
        """
        user = await self.get(id_)
        return await self._update(user, data)

    async def delete(self, id_: UUID) -> None:
        """Delete a user from the database.

        Args:
            id_: UUID corresponding to a user primary key.
        """
        record = await self.get(id_)
        await self.session.delete(record)
        await self.session.commit()

    async def _update(self, user: UserModelType, data: Dict[str, Any]) -> UserModelType:
        for attr, val in data.items():
            setattr(user, attr, val)

        await self.session.commit()
        return user
