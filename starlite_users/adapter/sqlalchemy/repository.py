from __future__ import annotations

from typing import TYPE_CHECKING, Generic

from starlite.contrib.sqlalchemy.repository import SQLAlchemyRepository

from starlite_users.adapter.sqlalchemy.mixins import (
    RoleModelType,
    UserModelType,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["SQLAlchemyRoleRepository", "SQLAlchemyUserRepository"]


class SQLAlchemyUserRepository(SQLAlchemyRepository[UserModelType], Generic[UserModelType]):
    """SQLAlchemy implementation of user persistence layer."""

    def __init__(self, session: AsyncSession, user_model: type[UserModelType]) -> None:
        """Repository for users.

        Args:
            session: Session managing the unit-of-work for the operation.
            user_model: A subclass of `SQLAlchemyUserModel`.
        """
        super().__init__(session)
        self.model_type = user_model


class SQLAlchemyRoleRepository(SQLAlchemyRepository[RoleModelType], Generic[RoleModelType, UserModelType]):
    """SQLAlchemy implementation of role persistence layer."""

    def __init__(self, session: AsyncSession, role_model: type[RoleModelType]) -> None:
        """Repository for users.

        Args:
            session: Session managing the unit-of-work for the operation.
            role_model: A subclass of `SQLAlchemyRoleModel`.
        """
        super().__init__(session)
        self.model_type = role_model

    async def assign_role_to_user(self, user: UserModelType, role: RoleModelType) -> UserModelType:
        """Add a role to a user.

        Args:
            user: The user to receive the role.
            role: The role to add to the user.
        """
        user.roles.append(role)
        await self.session.commit()
        return user

    async def revoke_role_from_user(self, user: UserModelType, role: RoleModelType) -> UserModelType:
        """Revoke a role to a user.

        Args:
            user: The user to revoke the role from.
            role: The role to revoke from the user.
        """
        user.roles.remove(role)
        await self.session.commit()
        return user
