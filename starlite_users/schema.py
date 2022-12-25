from typing import List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, SecretStr


class BaseRoleReadDTO(BaseModel):
    id: UUID
    name: str
    description: str

    class Config:
        orm_mode = True


class BaseRoleCreateDTO(BaseModel):
    name: str
    description: str


class BaseRoleUpdateDTO(BaseModel):
    name: Optional[str]
    description: Optional[str]


class BaseUserReadDTO(BaseModel):
    id: UUID
    email: str
    roles: List[Optional[BaseRoleReadDTO]]
    is_active: bool
    is_verified: bool

    class Config:
        orm_mode = True


class BaseUserCreateDTO(BaseModel):
    email: str
    password: SecretStr
    is_active: Optional[bool]
    is_verified: Optional[bool]


class BaseUserUpdateDTO(BaseModel):
    email: Optional[str]
    password: Optional[SecretStr]
    is_active: Optional[bool]
    is_verified: Optional[bool]


class UserAuthSchema(BaseModel):
    email: str
    password: SecretStr


class ForgotPasswordSchema(BaseModel):
    email: str


class ResetPasswordSchema(BaseModel):
    token: str
    password: SecretStr


class UserRoleSchema(BaseModel):
    user_id: UUID
    role_id: UUID


RoleCreateDTOType = TypeVar("RoleCreateDTOType", bound=BaseRoleCreateDTO)
RoleReadDTOType = TypeVar("RoleReadDTOType", bound=BaseRoleReadDTO)
RoleUpdateDTOType = TypeVar("RoleUpdateDTOType", bound=BaseRoleUpdateDTO)

UserCreateDTOType = TypeVar("UserCreateDTOType", bound=BaseUserCreateDTO)
UserReadDTOType = TypeVar("UserReadDTOType", bound=BaseUserReadDTO)
UserUpdateDTOType = TypeVar("UserUpdateDTOType", bound=BaseUserUpdateDTO)
