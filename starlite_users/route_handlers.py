from typing import Optional
from uuid import UUID

from starlite import post, get, put, delete

from .models import User
from .schema import UserCreateDTO, UserReadDTO, UserUpdateDTO
from .service import UserService

IDENTIFIER_URI = '/{id_:uuid}'  # TODO: define via config


@post('/register')  # TODO: make configurable
async def register(data: UserCreateDTO) -> UserReadDTO:
    pass


@post('/login')  # TODO: make configurable
async def login(data: UserReadDTO) -> UserReadDTO:
    pass


@get('/user/me')  # TODO: make configurable
async def get_current_user() -> Optional[User]:
    pass


@get(IDENTIFIER_URI)
async def get_user(id_: UUID, service: UserService) -> UserReadDTO:  # TODO: add before/after hooks
    user = await service.get(id_)
    return UserReadDTO.from_orm(user)


@put(IDENTIFIER_URI)
async def update_user(id_: UUID, data: UserUpdateDTO, service: UserService) -> UserReadDTO:  # TODO: add before/after hooks
    user = await service.update(id_, data)
    return UserReadDTO.from_orm(user)


@delete(IDENTIFIER_URI)
async def delete_user(id_: UUID, service: UserService) -> None:  # TODO: add before/after hooks
    return await service.delete(id_)
