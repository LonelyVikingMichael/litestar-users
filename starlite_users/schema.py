from typing import List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, SecretStr


class RoleReadDTO(BaseModel):
    id: UUID
    name: str
    description: str

    class Config:
        orm_mode = True


class RoleCreateDTO(BaseModel):
    name: str
    description: str


class RoleUpdateDTO(BaseModel):
    name: Optional[str]
    description: Optional[str]


class UserReadDTO(BaseModel):
    id: UUID
    email: str
    roles: List[Optional[RoleReadDTO]]
    is_active: bool
    is_verified: bool

    class Config:
        orm_mode = True


class UserCreateDTO(BaseModel):
    email: str
    password: SecretStr
    is_active: Optional[bool] = True
    is_verified: Optional[bool] = False


class UserUpdateDTO(BaseModel):
    email: Optional[str]
    password: Optional[SecretStr]
    is_active: Optional[bool]
    is_verified: Optional[bool]


class UserAuthSchema(BaseModel):
    email: str
    password: SecretStr


CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
ReadSchemaType = TypeVar('ReadSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)
