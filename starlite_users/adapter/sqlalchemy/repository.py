from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic

from litestar.contrib.sqlalchemy.repository import SQLAlchemyRepository

from starlite_users.adapter.abc import AbstractRoleRepository, AbstractUserRepository
from starlite_users.adapter.sqlalchemy.protocols import SQLARoleT, SQLAUserT

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["SQLAlchemyRoleRepository", "SQLAlchemyUserRepository"]


class SQLAlchemyUserRepository(AbstractUserRepository[SQLAUserT], SQLAlchemyRepository[SQLAUserT], Generic[SQLAUserT]):
    """SQLAlchemy implementation of user persistence layer."""

    def __init__(self, session: AsyncSession, user_model: type[SQLAUserT]) -> None:
        """Repository for users.

        Args:
            session: Session managing the unit-of-work for the operation.
            user_model: A subclass of `SQLAlchemyUserModel`.
        """
        super().__init__(session=session)
        self.model_type = user_model

    async def _update(self, user: SQLAUserT, data: dict[str, Any]) -> SQLAUserT:
        for key, value in data.items():
            setattr(user, key, value)

        await self.session.commit()
        return user


class SQLAlchemyRoleRepository(
    AbstractRoleRepository[SQLARoleT, SQLAUserT], SQLAlchemyRepository[SQLARoleT], Generic[SQLARoleT, SQLAUserT]
):
    """SQLAlchemy implementation of role persistence layer."""

    def __init__(self, session: AsyncSession, role_model: type[SQLARoleT]) -> None:
        """Repository for users.

        Args:
            session: Session managing the unit-of-work for the operation.
            role_model: A subclass of `SQLAlchemyRoleModel`.
        """
        super().__init__(session=session)
        self.model_type = role_model

    async def assign_role(self, user: SQLAUserT, role: SQLARoleT) -> SQLAUserT:
        """Add a role to a user.

        Args:
            user: The user to receive the role.
            role: The role to add to the user.
        """
        user.roles.append(role)  # pyright: ignore
        await self.session.commit()
        return user

    async def revoke_role(self, user: SQLAUserT, role: SQLARoleT) -> SQLAUserT:
        """Revoke a role from a user.

        Args:
            user: The user to revoke the role from.
            role: The role to revoke from the user.
        """
        user.roles.remove(role)  # pyright: ignore
        await self.session.commit()
        return user
