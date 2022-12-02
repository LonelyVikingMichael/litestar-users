from typing import Optional, TypeVar

from pydantic import BaseModel


class UserReadDTO(BaseModel):
    email: str


class UserCreateDTO(BaseModel):
    email: str
    password: str


class UserUpdateDTO(BaseModel):
    email: Optional[str]
    password: Optional[str]


CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
ReadSchemaType = TypeVar('ReadSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)
