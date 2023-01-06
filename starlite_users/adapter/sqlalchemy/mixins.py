from typing import TYPE_CHECKING, List, TypeVar
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm.decl_api import declarative_mixin, declared_attr

from starlite_users.adapter.sqlalchemy.guid import GUID  # pylint: disable=E0401

if TYPE_CHECKING:
    from sqlalchemy.orm.attributes import Mapped  # type: ignore[attr-defined]


@declarative_mixin
class SQLAlchemyUserMixin:
    """Base SQLAlchemy user mixin with `roles` attribute."""

    __tablename__ = "user"

    id: "Mapped[UUID]" = Column(
        GUID(),
        primary_key=True,
        default=uuid4,
        unique=True,
        nullable=False,
    )
    email: "Mapped[str]" = Column(String(320), nullable=False, unique=True)
    password_hash: "Mapped[str]" = Column(String(1024))
    is_active: "Mapped[bool]" = Column(Boolean(), nullable=False, default=False)
    is_verified: "Mapped[bool]" = Column(Boolean(), nullable=False, default=False)

    @declared_attr  # type: ignore[misc]
    def roles(cls) -> "Mapped[List[RoleModelType]]":  # pylint: disable=E0213
        """Roles attribute."""

        return relationship("Role", secondary="user_roles", lazy="joined")  # type: ignore[misc]


@declarative_mixin
class SQLAlchemyRoleMixin:
    """Base SQLAlchemy role mixin."""

    __tablename__ = "role"

    id: "Mapped[UUID]" = Column(
        GUID(),
        primary_key=True,
        default=uuid4,
        unique=True,
        nullable=False,
    )
    name: "Mapped[str]" = Column(String(255), nullable=False, unique=True)
    description: "Mapped[str]" = Column(String(255), nullable=True)


@declarative_mixin
class UserRoleAssociationMixin:
    """Base SQLAlchemy `user.roles` association mixin."""

    __tablename__ = "user_roles"

    @declared_attr  # type: ignore[misc]
    def role_id(cls) -> "Mapped[UUID]":  # pylint: disable=E0213
        """Id attribute."""

        return Column(GUID(), ForeignKey("role.id"), nullable=True)

    @declared_attr  # type: ignore[misc]
    def user_id(cls) -> "Mapped[UUID]":  # pylint: disable=E0213
        """Id attribute."""

        return Column(GUID(), ForeignKey("user.id"), nullable=True)


UserModelType = TypeVar("UserModelType", bound=SQLAlchemyUserMixin)
RoleModelType = TypeVar("RoleModelType", bound=SQLAlchemyRoleMixin)
