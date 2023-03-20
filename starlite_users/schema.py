from __future__ import annotations

from typing import TypeVar
from uuid import UUID  # noqa: TCH003

from pydantic import BaseModel, SecretStr

__all__ = [
    "BaseRoleCreateDTO",
    "BaseRoleReadDTO",
    "BaseRoleUpdateDTO",
    "BaseUserCreateDTO",
    "BaseUserReadDTO",
    "BaseUserRoleReadDTO",
    "BaseUserUpdateDTO",
    "ForgotPasswordSchema",
    "ResetPasswordSchema",
    "UserAuthSchema",
    "UserRoleSchema",
]


class BaseRoleReadDTO(BaseModel):
    """Base role read schema."""

    id: UUID
    name: str
    description: str

    class Config:
        orm_mode = True


class BaseRoleCreateDTO(BaseModel):
    """Base role create schema."""

    name: str
    description: str


class BaseRoleUpdateDTO(BaseModel):
    """Base role update schema."""

    name: str | None
    description: str | None


class BaseUserReadDTO(BaseModel):
    """Base user read schema."""

    id: UUID
    email: str
    is_active: bool
    is_verified: bool

    class Config:
        orm_mode = True


class BaseUserRoleReadDTO(BaseUserReadDTO):
    """Base user read schema that includes `roles`."""

    roles: list[BaseRoleReadDTO | None]


class BaseUserCreateDTO(BaseModel):
    """Base user create schema."""

    email: str
    password: SecretStr
    is_active: bool | None
    is_verified: bool | None


class BaseUserUpdateDTO(BaseModel):
    """Base user update schema."""

    email: str | None
    password: SecretStr | None
    is_active: bool | None
    is_verified: bool | None


class UserAuthSchema(BaseModel):
    """User authentication schema."""

    email: str
    password: SecretStr


class ForgotPasswordSchema(BaseModel):
    """Forgot password schema."""

    email: str


class ResetPasswordSchema(BaseModel):
    """Reset password schema."""

    token: str
    password: SecretStr


class UserRoleSchema(BaseModel):
    """User role association schema."""

    user_id: UUID
    role_id: UUID


RoleCreateDTOType = TypeVar("RoleCreateDTOType", bound=BaseRoleCreateDTO)
RoleReadDTOType = TypeVar("RoleReadDTOType", bound=BaseRoleReadDTO)
RoleUpdateDTOType = TypeVar("RoleUpdateDTOType", bound=BaseRoleUpdateDTO)

UserCreateDTOType = TypeVar("UserCreateDTOType", bound=BaseUserCreateDTO)
UserReadDTOType = TypeVar("UserReadDTOType", bound=BaseUserReadDTO)
UserUpdateDTOType = TypeVar("UserUpdateDTOType", bound=BaseUserUpdateDTO)
