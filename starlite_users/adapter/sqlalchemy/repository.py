from typing import TYPE_CHECKING, Any, Dict, Generic, Type, cast

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound  # type: ignore[attr-defined]
from starlite.exceptions import ImproperlyConfiguredException

from starlite_users.adapter.sqlalchemy.mixins import (
    RoleModelType,
    UserModelType,
    UserRoleModelType,
)
from starlite_users.exceptions import (
    RepositoryConflictException,
    RepositoryNotFoundException,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SQLAlchemyUserRepository(Generic[UserModelType]):  # TODO: create generic base for piccolo, tortoise etc
    """SQLAlchemy implementation of user persistence layer."""

    user_model_type: Type[UserModelType]

    def __init__(
        self,
        session: "AsyncSession",
        user_model_type: Type[UserModelType],
    ) -> None:
        """Initialise a repository instance.

        Args:
            session: A SQLAlchemy `AsyncSession`.
            user_model_type: A subclass of [SQLAlchemyUserMixin][starlite_users.adapter.sqlalchemy.mixins.SQLAlchemyUserMixin]
        """
        self.session = session
        self.user_model = user_model_type

    async def add_user(self, user: UserModelType) -> UserModelType:
        """Add a user to the database.

        Args:
            user: A SQLAlchemy User model instance.

        Raises:
            RepositoryConflictException: when the given user already exists.
        """
        try:
            self.session.add(user)
            await self.session.flush()
            await self.session.refresh(user)

            await self.session.commit()

            return user
        except IntegrityError as e:
            raise RepositoryConflictException from e

    async def get_user(self, id_: "UUID") -> UserModelType:
        """Retrieve a user from the database by id.

        Args:
            id_: UUID corresponding to a user primary key.

        Raises:
            RepositoryNotFoundException: when no user matches the query.
        """
        result = await self.session.execute(select(self.user_model).where(self.user_model.id == id_))  # type: ignore[arg-type, attr-defined]
        try:
            return cast("UserModelType", result.unique().scalar_one())
        except NoResultFound as e:
            raise RepositoryNotFoundException from e

    async def get_user_by(self, **kwargs: Any) -> UserModelType:
        """Retrieve a user from the database by arbitrary keyword arguments.

        Args:
            **kwargs: Keyword arguments to pass as filters.

        Examples:
            ```python
            repository = SQLAlchemyUserRepository(...)
            john = await repository.get_user_by(email="john@example.com")
            ```

        Raises:
            RepositoryNotFoundException: when no user matches the query.
        """
        result = await self.session.execute(
            select(self.user_model).where(*(getattr(self.user_model, k) == v for k, v in kwargs.items()))  # type: ignore[arg-type]
        )
        try:
            return cast("UserModelType", result.unique().scalar_one())
        except NoResultFound as e:
            raise RepositoryNotFoundException from e

    async def update_user(self, id_: "UUID", data: Dict[str, Any]) -> UserModelType:
        """Update arbitrary user attributes in the database.

        Args:
            id_: UUID corresponding to a user primary key.
            data: Dictionary to map to user columns and values.
        """
        user = await self.get_user(id_)
        return await self._update(user, data)

    async def delete_user(self, id_: "UUID") -> None:
        """Delete a user from the database.

        Args:
            id_: UUID corresponding to a user primary key.
        """
        user = await self.get_user(id_)
        await self.session.delete(user)
        await self.session.commit()

    async def _update(self, user: UserModelType, data: Dict[str, Any]) -> UserModelType:
        for attr, val in data.items():
            setattr(user, attr, val)

        await self.session.commit()
        return user


class SQLAlchemyUserRoleRepository(
    SQLAlchemyUserRepository[UserRoleModelType], Generic[UserRoleModelType, RoleModelType]
):
    """SQLAlchemy implementation of user persistence layer with roles."""

    def __init__(
        self,
        session: "AsyncSession",
        user_model_type: Type[UserRoleModelType],
        role_model_type: Type[RoleModelType],
    ) -> None:
        """Initialise a repository instance.

        Args:
            session: A SQLAlchemy `AsyncSession`.
            user_model_type: A subclass of [SQLAlchemyUserRoleMixin][starlite_users.adapter.sqlalchemy.mixins.SQLAlchemyUserRoleMixin]
            role_model_type: A subclass of [SQLAlchemyRoleMixin][starlite_users.adapter.sqlalchemy.mixins.SQLAlchemyRoleMixin]
        """
        self.session = session
        self.user_model = user_model_type
        self.role_model = role_model_type

    async def add_role(self, role: RoleModelType) -> RoleModelType:
        """Add a role to the database.

        Args:
            role: A SQLAlchemy Role model instance.

        Raises:
            RepositoryConflictException: when the given role already exists.
        """
        try:
            self.session.add(role)
            await self.session.flush()
            await self.session.refresh(role)

            await self.session.commit()

            return role
        except IntegrityError as e:
            raise RepositoryConflictException from e

    async def assign_role_to_user(self, user: UserRoleModelType, role: RoleModelType) -> UserRoleModelType:
        """Add a role to a user.

        Args:
            user: The user to receive the role.
            role: The role to add to the user.
        """
        user.roles.append(role)
        await self.session.commit()
        return user

    async def revoke_role_from_user(self, user: UserRoleModelType, role: RoleModelType) -> UserRoleModelType:
        """Revoke a role to a user.

        Args:
            user: The user to revoke the role from.
            role: The role to revoke from the user.
        """
        user.roles.remove(role)
        await self.session.commit()
        return user

    async def get_role(self, id_: "UUID") -> RoleModelType:
        """Retrieve a role from the database by id.

        Args:
            id_: UUID corresponding to a role primary key.

        Raises:
            RepositoryNotFoundException: when no role matches the query.
        """
        if self.role_model is None:
            raise ImproperlyConfiguredException("self.role_model is not configured")
        result = await self.session.execute(select(self.role_model).where(self.role_model.id == id_))  # type: ignore[arg-type]
        try:
            return cast("RoleModelType", result.unique().scalar_one())
        except NoResultFound as e:
            raise RepositoryNotFoundException from e

    async def get_role_by_name(self, name: str) -> RoleModelType:
        """Retrieve a role from the database by name.

        Args:
            name: The name of the desired role record.

        Raises:
            RepositoryNotFoundException: when no role matches the query.
        """
        if self.role_model is None:
            raise ImproperlyConfiguredException("self.role_model is not configured")
        result = await self.session.execute(select(self.role_model).where(self.role_model.name == name))  # type: ignore[arg-type]
        try:
            return cast("RoleModelType", result.unique().scalar_one())
        except NoResultFound as e:
            raise RepositoryNotFoundException from e

    async def update_role(self, id_: "UUID", data: Dict[str, Any]) -> RoleModelType:
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

    async def delete_role(self, id_: "UUID") -> None:
        """Delete a role from the database.

        Args:
            id_: UUID corresponding to a role primary key.
        """
        role = await self.get_user(id_)
        await self.session.delete(role)
        await self.session.commit()
