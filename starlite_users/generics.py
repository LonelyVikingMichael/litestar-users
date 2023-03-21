from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar

if TYPE_CHECKING:
    from uuid import UUID

__all__ = ["AbstractUserRepository", "RoleProtocol", "UserProtocol"]


class UserProtocol(Protocol):
    """Base protocol to be inherited when implementing user model mixins."""

    id: UUID
    email: str
    password_hash: str
    is_active: bool
    is_verified: bool


class RoleProtocol(Protocol):
    """Base protocol to be inherited when implementing role model mixins."""

    id: UUID
    name: str
    description: str


UserT = TypeVar("UserT", bound=UserProtocol)
RoleT = TypeVar("RoleT", bound=RoleProtocol)


class AbstractUserRepository(ABC, Generic[UserT, RoleT]):
    """Base protocol to be inherited when implementing repositories."""

    user_model: type[UserT]
    role_model: type[RoleT]

    def __init__(self, **kwargs: Any) -> None:
        ...

    @abstractmethod
    async def add_user(self, user: UserT) -> UserT:
        """Add a user to the database.

        Args:
            user: A SQLAlchemy User model instance.

        Raises:
            RepositoryConflictException: when the given user already exists.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_user(self, id_: UUID) -> UserT:
        """Retrieve a user from the database by id.

        Args:
            id_: UUID corresponding to a user primary key.

        Raises:
            RepositoryNotFoundException: when no user matches the query.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_user_by(self, **kwargs: Any) -> UserT:
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
        raise NotImplementedError()

    @abstractmethod
    async def update_user(self, id_: UUID, data: dict[str, Any]) -> UserT:
        """Update arbitrary user attributes in the database.

        Args:
            id_: UUID corresponding to a user primary key.
            data: Dictionary to map to user columns and values.
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete_user(self, id_: UUID) -> None:
        """Delete a user from the database.

        Args:
            id_: UUID corresponding to a user primary key.
        """
        raise NotImplementedError()

    @abstractmethod
    async def _update(self, user: UserT, data: dict[str, Any]) -> UserT:
        raise NotImplementedError()

    @abstractmethod
    async def add_role(self, role: RoleT) -> RoleT:
        """Add a role to the database.

        Args:
            role: A SQLAlchemy Role model instance.

        Raises:
            RepositoryConflictException: when the given role already exists.
        """
        raise NotImplementedError()

    @abstractmethod
    async def assign_role_to_user(self, user: UserT, role: RoleT) -> UserT:
        """Add a role to a user.

        Args:
            user: The user to receive the role.
            role: The role to add to the user.
        """
        raise NotImplementedError()

    @abstractmethod
    async def revoke_role_from_user(self, user: UserT, role: RoleT) -> UserT:
        """Revoke a role to a user.

        Args:
            user: The user to revoke the role from.
            role: The role to revoke from the user.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_role(self, id_: UUID) -> RoleT:
        """Retrieve a role from the database by id.

        Args:
            id_: UUID corresponding to a role primary key.

        Raises:
            RepositoryNotFoundException: when no role matches the query.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_role_by_name(self, name: str) -> RoleT:
        """Retrieve a role from the database by name.

        Args:
            name: The name of the desired role record.

        Raises:
            RepositoryNotFoundException: when no role matches the query.
        """
        raise NotImplementedError()

    @abstractmethod
    async def update_role(self, id_: UUID, data: dict[str, Any]) -> RoleT:
        """Update arbitrary role attributes in the database.

        Args:
            id_: UUID corresponding to a role primary key.
            data: Dictionary to map to role columns and values.
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete_role(self, id_: UUID) -> None:
        """Delete a role from the database.

        Args:
            id_: UUID corresponding to a role primary key.
        """
        raise NotImplementedError()
