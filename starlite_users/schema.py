from typing import List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, SecretStr


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

    name: Optional[str]
    description: Optional[str]


class BaseUserReadDTO(BaseModel):
    """Base user read schema."""

    id: UUID
    email: str
    roles: List[Optional[BaseRoleReadDTO]]
    is_active: bool
    is_verified: bool

    class Config:
        orm_mode = True


class BaseUserCreateDTO(BaseModel):
    """Base user create schema."""

    email: str
    password: SecretStr
    is_active: Optional[bool]
    is_verified: Optional[bool]


class BaseUserUpdateDTO(BaseModel):
    """Base user update schema."""

    email: Optional[str]
    password: Optional[SecretStr]
    is_active: Optional[bool]
    is_verified: Optional[bool]


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
