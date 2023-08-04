from dataclasses import dataclass
from typing import TypeVar
from uuid import UUID

__all__ = [
    "ForgotPasswordSchema",
    "ResetPasswordSchema",
    "RoleCreateDTOType",
    "RoleReadDTOType",
    "RoleUpdateDTOType",
    "AuthenticationSchema",
    "UserCreateDTOType",
    "UserReadDTOType",
    "UserRoleSchema",
    "UserUpdateDTOType",
]

@dataclass
class AuthenticationSchema:
    """User authentication schema."""

    email: str
    password: str


@dataclass
class ForgotPasswordSchema:
    """Forgot password schema."""

    email: str


@dataclass
class ResetPasswordSchema:
    """Reset password schema."""

    token: str
    password: str


@dataclass
class UserRoleSchema:
    """User role association schema."""

    user_id: UUID
    role_id: UUID


RoleCreateDTOType = TypeVar("RoleCreateDTOType")
RoleReadDTOType = TypeVar("RoleReadDTOType")
RoleUpdateDTOType = TypeVar("RoleUpdateDTOType")

UserCreateDTOType = TypeVar("UserCreateDTOType")
UserReadDTOType = TypeVar("UserReadDTOType")
UserUpdateDTOType = TypeVar("UserUpdateDTOType")
