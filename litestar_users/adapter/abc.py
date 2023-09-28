from __future__ import annotations

from abc import abstractmethod
from typing import Any, Generic, TypeVar

from litestar.repository.abc import AbstractAsyncRepository

__all__ = ["AbstractRoleRepository", "AbstractUserRepository"]


T = TypeVar("T")
R = TypeVar("R")
URepoT = TypeVar("URepoT", bound="AbstractUserRepository")


class AbstractUserRepository(AbstractAsyncRepository[T], Generic[T]):
    """Interface for user persistence interaction."""

    @abstractmethod
    async def _update(self, user: T, data: dict[str, Any]) -> T:
        """Update a user that is already present in the db session."""


class AbstractRoleRepository(AbstractAsyncRepository[R], Generic[R, T]):
    """Interface for role persistence interaction."""

    @abstractmethod
    async def assign_role(self, user: T, role: R) -> T:
        """Add a role to a user.

        Args:
            user: The user to receive the role.
            role: The role to add to the user.
        """

    @abstractmethod
    async def revoke_role(self, user: T, role: R) -> T:
        """Revoke a role from a user.

        Args:
            user: The user to revoke the role from.
            role: The role to revoke from the user.
        """
