from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from litestar.exceptions import ImproperlyConfiguredException

from litestar_users.adapter.sqlalchemy.protocols import SQLARoleT, SQLAUserT

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["SQLAlchemyRoleRepository", "SQLAlchemyUserRepository"]


class SQLAlchemyUserRepository(SQLAlchemyAsyncRepository[SQLAUserT], Generic[SQLAUserT]):
    """SQLAlchemy implementation of user persistence layer."""

    def __init__(self, session: AsyncSession, model_type: type[SQLAUserT]) -> None:
        """Repository for users.

        Args:
            session: Session managing the unit-of-work for the operation.
            model_type: A subclass of `SQLAlchemyUserModel`.
        """
        self.model_type = model_type
        super().__init__(session=session)

    async def _update(self, user: SQLAUserT, data: dict[str, Any]) -> SQLAUserT:
        for key, value in data.items():
            setattr(user, key, value)

        await self.session.commit()
        return user


class SQLAlchemyRoleRepository(SQLAlchemyAsyncRepository[SQLARoleT], Generic[SQLARoleT, SQLAUserT]):
    """SQLAlchemy implementation of role persistence layer."""

    def __init__(self, session: AsyncSession, model_type: type[SQLARoleT]) -> None:
        """Repository for users.

        Args:
            session: Session managing the unit-of-work for the operation.
            model_type: A subclass of `SQLAlchemyRoleModel`.
        """
        self.model_type = model_type
        super().__init__(session=session)

    async def assign_role(self, user: SQLAUserT, role: SQLARoleT) -> SQLAUserT:
        """Add a role to a user.

        Args:
            user: The user to receive the role.
            role: The role to add to the user.
        """
        if not hasattr(user, "roles"):
            raise ImproperlyConfiguredException("User.roles is not set")
        user.roles.append(role)  # pyright: ignore
        await self.session.commit()
        return user

    async def revoke_role(self, user: SQLAUserT, role: SQLARoleT) -> SQLAUserT:
        """Revoke a role from a user.

        Args:
            user: The user to revoke the role from.
            role: The role to revoke from the user.
        """
        if not hasattr(user, "roles"):
            raise ImproperlyConfiguredException("User.roles is not set")
        user.roles.remove(role)  # pyright: ignore
        await self.session.commit()
        return user
