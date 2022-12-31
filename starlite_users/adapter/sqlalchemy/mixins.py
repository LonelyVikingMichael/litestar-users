from typing import TypeVar
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import Mapped, declarative_mixin, declared_attr, relationship

from .guid import GUID


@declarative_mixin
class SQLAlchemyUserMixin:
    __tablename__ = "user"

    id: Mapped[UUID] = Column(
        GUID(),
        primary_key=True,
        default=uuid4,
        unique=True,
        nullable=False,
    )
    email: Mapped[str] = Column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = Column(String(1024))
    is_active: Mapped[bool] = Column(Boolean(), nullable=False, default=False)
    is_verified: Mapped[bool] = Column(Boolean(), nullable=False, default=False)

    @declared_attr
    def roles(self):
        return relationship("Role", secondary="user_roles", lazy="joined")


@declarative_mixin
class SQLAlchemyRoleMixin:
    __tablename__ = "role"

    id: Mapped[UUID] = Column(
        GUID(),
        primary_key=True,
        default=uuid4,
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = Column(String(255), nullable=False, unique=True)
    description: Mapped[str] = Column(String(255), nullable=True)


@declarative_mixin
class UserRoleAssociationMixin:
    __tablename__ = "user_roles"

    @declared_attr
    def role_id(self):
        return Column(GUID(), ForeignKey("role.id"), nullable=True)

    @declared_attr
    def user_id(self):
        return Column(GUID(), ForeignKey("user.id"), nullable=True)


UserModelType = TypeVar("UserModelType", bound=SQLAlchemyUserMixin)
RoleModelType = TypeVar("RoleModelType", bound=SQLAlchemyRoleMixin)
