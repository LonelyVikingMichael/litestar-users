from typing import Any, Dict, Generic, Optional, Type
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from starlite_users.exceptions import (
    RoleConflictException,
    RoleNotFoundException,
    UserConflictException,
    UserNotFoundException,
)

from .models import RoleModelType, UserModelType


class SQLAlchemyUserRepository(Generic[UserModelType]):  # TODO: create generic base for piccolo, tortoise etc
    """SQLAlchemy implementation of user persistence layer."""

    user_model_type: Type[UserModelType]
    role_model_type: Type[RoleModelType]

    def __init__(
        self, session: AsyncSession, user_model_type: Type[UserModelType], role_model_type: Type[RoleModelType]
    ) -> None:
        """Initialise a repository instance.

        Args:
            session: A SQLAlchemy `AsyncSession`.
            user_model_type: A subclass of [SQLAlchemyUser][starlite_users.models.SQLAlchemyUser]
        """
        self.session = session
        self.user_model = user_model_type
        self.role_model = role_model_type

    async def add(self, user: UserModelType) -> UserModelType:
        """Add a user to the database.

        Args:
            user: A SQLAlchemy User model instance.

        Raises:
            UserConflictException: when the given user already exists.
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
        result = await self.session.execute(select(self.user_model).where(self.user_model.id == id_))
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
            select(self.user_model).where(*(getattr(self.user_model, k) == v for k, v in kwargs.items()))
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
        user = await self.get(id_)
        await self.session.delete(user)
        await self.session.commit()

    async def _update(self, user: UserModelType, data: Dict[str, Any]) -> UserModelType:
        for attr, val in data.items():
            setattr(user, attr, val)

        await self.session.commit()
        return user

    async def add_role(self, role: RoleModelType) -> RoleModelType:
        """Add a role to the database.

        Args:
            role: A SQLAlchemy Role model instance.

        Raises:
            RoleConflictException: when the given role already exists.
        """
        try:
            self.session.add(role)
            await self.session.flush()
            await self.session.refresh(role)

            await self.session.commit()

            return role
        except IntegrityError as e:
            raise RoleConflictException from e

    async def add_role_to_user(self, user: UserModelType, role: RoleModelType) -> UserModelType:
        user.roles.append(role)
        await self.session.commit()
        return user

    async def get_role(self, id_: UUID) -> RoleModelType:
        """Retrieve a role from the database by id.

        Args:
            id_: UUID corresponding to a role primary key.

        Raises:
            RoleNotFoundException: when no role matches the query.
        """
        result = await self.session.execute(select(self.role_model).where(self.role_model.id == id_))
        try:
            return result.unique().scalar_one()
        except NoResultFound as e:
            raise RoleNotFoundException from e

    async def get_role_by_name(self, name: str) -> RoleModelType:
        """Retrieve a role from the database by name.

        Args:
            name: The name of the desired role record.

        Raises:
            RoleNotFoundException: when no role matches the query.
        """
        result = await self.session.execute(select(self.role_model).where(self.role_model.name == name))
        try:
            return result.unique().scalar_one()
        except NoResultFound as e:
            raise RoleNotFoundException from e

    async def update_role(self, id_: UUID, data: Dict[str, Any]) -> RoleModelType:
        """Update arbitrary role attributes in the database.

        Args:
            id_: UUID corresponding to a role primary key.
            data: Dictionary to map to role columns and values.
        """
        role = await self.get_role(id_)
        for attr, val in data.items():
            setattr(role, attr, val)

        await self.session.commit()
        return role

    async def delete_role(self, id_: UUID) -> None:
        """Delete a role from the database.

        Args:
            id_: UUID corresponding to a role primary key.
        """
        role = await self.get(id_)
        await self.session.delete(role)
        await self.session.commit()
