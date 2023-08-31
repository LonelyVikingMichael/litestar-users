from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar, runtime_checkable

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Mapped

__all__ = ["RoleModelProtocol", "UserModelProtocol", "UserRegisterT"]

UserT = TypeVar("UserT", bound="UserModelProtocol")
RoleT = TypeVar("RoleT", bound="RoleModelProtocol")
UserRegisterT = TypeVar("UserRegisterT", bound="UserRegistrationProtocol")


@runtime_checkable
class RoleModelProtocol(Protocol):
    """The base role type."""

    id: UUID | Mapped[UUID]
    name: str | Mapped[str]
    description: str | Mapped[str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ...


@runtime_checkable
class UserModelProtocol(Protocol):
    """The base user type."""

    id: UUID
    email: str
    password_hash: str
    is_active: bool
    is_verified: bool
    roles: list

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        ...


@runtime_checkable
class UserRegistrationProtocol(Protocol):
    """The minimum fields required on user registration/creation."""

    email: str
    password: str
