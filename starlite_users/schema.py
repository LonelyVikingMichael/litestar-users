from typing import Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, SecretStr


class UserReadDTO(BaseModel):
    id: UUID
    email: str

    class Config:
        orm_mode = True


class UserCreateDTO(BaseModel):
    email: str
    password: SecretStr


class UserUpdateDTO(BaseModel):
    email: Optional[str]
    password: Optional[SecretStr]


class UserAuthSchema(BaseModel):
    email: str
    password: SecretStr


CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
ReadSchemaType = TypeVar('ReadSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)
