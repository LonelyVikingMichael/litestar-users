from typing import Optional, Dict, Literal
from uuid import UUID

from starlite import Provide, Request, Router, post, get, put, delete
from starlite.exceptions import NotAuthorizedException
from starlite import HTTPRouteHandler

from .models import User
from .schema import UserAuthSchema, UserCreateDTO, UserReadDTO, UserUpdateDTO
from .service import get_service, UserService

IDENTIFIER_URI = '/{id_:uuid}'  # TODO: define via config


def get_registration_handler(path: str = '/register') -> HTTPRouteHandler:
    @post(path, dependencies={'service': Provide(get_service)})
    async def register(data: UserCreateDTO, service: UserService) -> UserReadDTO:
        user = await service.add(data)
        return UserReadDTO.from_orm(user)
    return register


def get_verification_handler(path: str = '/verify') -> HTTPRouteHandler:
    @post(path)
    async def verify() -> None:
        # use pre-generated token
        # perhaps configure on service level
        pass
    return verify


def get_auth_handler(login_path: str = '/login', logout_path: str = '/logout') -> Router:
    @post(login_path, dependencies={'service': Provide(get_service)})  # TODO: make configurable
    async def login(
        data: UserAuthSchema, service: UserService, request: Request
    ) -> Optional[UserReadDTO]:
        user = await service.authenticate(data)
        if user is None:
            request.clear_session()
            raise NotAuthorizedException

        request.set_session({'user_id': user.id})  # TODO: move and make configurable
        return UserReadDTO.from_orm(user)

    @post(logout_path)
    async def logout(request: Request) -> None:
        request.clear_session()

    return Router(path='/', route_handlers=[login, logout])


@get('/user/me')  # TODO: make configurable
async def get_current_user(request: Request[User, Dict[Literal['user_id'], str]]) -> Optional[UserReadDTO]:
    return UserReadDTO.from_orm(request.user)


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


# user_router = Router(
#     path='/',
#     dependencies={'service': Provide(get_service)},
#     route_handlers=[
#         register,
#         login,
#         get_current_user,
#         get_user,
#         update_user,
#         delete_user
#     ]
# )
