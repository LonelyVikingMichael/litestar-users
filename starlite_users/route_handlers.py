from typing import Optional
from uuid import UUID

from starlite import Provide, Request, Router, post, get, put, delete
from starlite.exceptions import NotAuthorizedException

from .models import User
from .schema import UserAuthSchema, UserCreateDTO, UserReadDTO, UserUpdateDTO
from .service import get_service, UserService

IDENTIFIER_URI = '/{id_:uuid}'  # TODO: define via config


@post('/register')  # TODO: make configurable
async def register(data: UserCreateDTO, service: UserService) -> UserReadDTO:
    user = await service.add(data)
    return UserReadDTO.from_orm(user)


@post('/verify')  # TODO: make configurable
async def verify() -> None:
    # use pre-generated token
    # perhaps configure on service level
    pass


@post('/login')  # TODO: make configurable
async def login(
    data: UserAuthSchema, service: UserService, request: Request
) -> UserReadDTO:
    user = await service.authenticate(data)
    if user is None:
        raise NotAuthorizedException
    request.set_session({'user_id', user.id})  # TODO: move and make configurable

    return user


@get('/user/me')  # TODO: make configurable
async def get_current_user(service: UserService) -> Optional[User]:
    return None


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


user_router = Router(
    path='/',
    dependencies={'service': Provide(get_service)},
    route_handlers=[
        register,
        login,
        get_current_user,
        get_user,
        update_user,
        delete_user
    ]
)
