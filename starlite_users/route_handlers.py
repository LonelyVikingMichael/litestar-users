from typing import Optional, Callable, Dict, Literal, Any
from uuid import UUID

from starlite import Provide, Request, Router, post, get, put, delete
from starlite.exceptions import NotAuthorizedException
from starlite import HTTPRouteHandler, BaseRouteHandler

from .models import UserModelType
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
    @post(login_path, dependencies={'service': Provide(get_service)})
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


def get_current_user_handler(path: str = '/users/me') -> Router:
    @get(path)
    async def get_current_user(request: Request[UserModelType, Dict[Literal['user_id'], str]]) -> UserReadDTO:
        return UserReadDTO.from_orm(request.user)

    @put(path, dependencies={'service': Provide(get_service)})
    async def update_current_user(
        data: UserUpdateDTO,
        request: Request[UserModelType, Dict[Literal['user_id'], str]],
        service: UserService,
    ) -> Optional[UserReadDTO]:
        updated_user = await service.update(id_=request.user.id, data=data)
        return UserReadDTO.from_orm(updated_user)

    return Router(path='/', route_handlers=[get_current_user, update_current_user])


def roles_accepted(*roles) -> Callable:
    def roles_accepted_guard(request: Request[UserModelType, Any], _: BaseRouteHandler) -> None:
        for role in request.user.roles:
            if role.name in roles:
                return
        raise NotAuthorizedException()
    return roles_accepted_guard


def get_user_management_handler(path_prefix: str = '/users') -> Router:
    @get(IDENTIFIER_URI, guards=[roles_accepted('administrator')], dependencies={'service': Provide(get_service)})
    async def get_user(id_: UUID, service: UserService) -> UserReadDTO:  # TODO: add before/after hooks
        user = await service.get(id_)
        return UserReadDTO.from_orm(user)


    @put(IDENTIFIER_URI, guards=[roles_accepted('administrator')], dependencies={'service': Provide(get_service)})
    async def update_user(id_: UUID, data: UserUpdateDTO, service: UserService) -> UserReadDTO:  # TODO: add before/after hooks
        user = await service.update(id_, data)
        return UserReadDTO.from_orm(user)


    @delete(IDENTIFIER_URI, guards=[roles_accepted('administrator')], dependencies={'service': Provide(get_service)})
    async def delete_user(id_: UUID, service: UserService) -> None:  # TODO: add before/after hooks
        return await service.delete(id_)

    return Router(path=path_prefix, route_handlers=[get_user, update_user, delete_user])
