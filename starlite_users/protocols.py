from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar, runtime_checkable

if TYPE_CHECKING:
    from uuid import UUID

__all__ = ["RoleModelProtocol", "UserModelProtocol"]

UserT = TypeVar("UserT", bound="UserModelProtocol")
RoleT = TypeVar("RoleT", bound="RoleModelProtocol")


@runtime_checkable
class RoleModelProtocol(Protocol):
    """The base role type."""

    id: UUID
    name: str
    description: str

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
