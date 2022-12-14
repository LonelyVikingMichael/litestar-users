from typing import Any, Callable, Dict, Literal, Optional, Tuple, Type, TypeVar
from uuid import UUID

from starlite import Provide, Request, Router, post, get, put, delete
from starlite.exceptions import NotAuthorizedException
from starlite import HTTPRouteHandler, BaseRouteHandler

from .models import UserModelType
from .schema import (
    ForgotPasswordSchema,
    ResetPasswordSchema,
    UserAuthSchema,
    UserCreateDTOType,
    UserReadDTOType,
    UserUpdateDTOType,
)
from .service import get_service, UserService

IDENTIFIER_URI = '/{id_:uuid}'  # TODO: define via config

ServiceType = TypeVar('ServiceType', bound=UserService)


def get_registration_handler(path: str, user_read_dto: Type[UserReadDTOType]) -> HTTPRouteHandler:
    @post(path, dependencies={'service': Provide(get_service)})
    async def register(data: UserCreateDTOType, service: ServiceType) -> UserReadDTOType:
        user = await service.add(data)
        return user_read_dto.from_orm(user)
    return register


def get_verification_handler(path, user_read_dto: Type[UserReadDTOType]) -> HTTPRouteHandler:
    @get(path, dependencies={'service': Provide(get_service)})
    async def verify(token: str, service: ServiceType) -> None:
        user = await service.verify(token)
        return user_read_dto.from_orm(user)
    return verify


def get_auth_handler(
    login_path: str,
    logout_path: str,
    user_read_dto: Type[UserReadDTOType],
) -> Router:
    @post(login_path, dependencies={'service': Provide(get_service)})
    async def login(
        data: UserAuthSchema, service: ServiceType, request: Request
    ) -> Optional[UserReadDTOType]:
        user = await service.authenticate(data)
        if user is None:
            request.clear_session()
            raise NotAuthorizedException()

        request.set_session({'user_id': user.id})  # TODO: move and make configurable
        return user_read_dto.from_orm(user)

    @post(logout_path)
    async def logout(request: Request) -> None:
        request.clear_session()

    return Router(path='/', route_handlers=[login, logout])


def get_current_user_handler(path: str, user_read_dto: Type[UserReadDTOType]) -> Router:
    @get(path)
    async def get_current_user(request: Request[UserModelType, Dict[Literal['user_id'], str]]) -> UserReadDTOType:
        return user_read_dto.from_orm(request.user)

    @put(path, dependencies={'service': Provide(get_service)})
    async def update_current_user(
        data: UserUpdateDTOType,
        request: Request[UserModelType, Dict[Literal['user_id'], str]],
        service: ServiceType,
    ) -> Optional[UserReadDTOType]:
        updated_user = await service.update(id_=request.user.id, data=data)
        return user_read_dto.from_orm(updated_user)

    return Router(path='/', route_handlers=[get_current_user, update_current_user])


def get_password_reset_handler(forgot_path: str, reset_path: str) -> Router:
    @post(forgot_path, dependencies={'service': Provide(get_service)})
    async def forgot_password(data: ForgotPasswordSchema, service: ServiceType) -> None:
        await service.initiate_password_reset(data.email)
        return

    @post(reset_path, dependencies={'service': Provide(get_service)})
    async def reset_password(data: ResetPasswordSchema, service: ServiceType) -> None:
        await service.reset_password(data.token, data.password)
        return

    return Router(path='/', route_handlers=[forgot_password, reset_password])


def roles_accepted(*roles: str) -> Callable:
    def roles_accepted_guard(request: Request[UserModelType, Any], _: BaseRouteHandler) -> None:
        if any(role.name in roles for role in request.user.roles):
            return
        raise NotAuthorizedException()
    return roles_accepted_guard


def get_user_management_handler(path_prefix: str, authorized_roles: Tuple[str], user_read_dto: Type[UserReadDTOType]) -> Router:
    @get(IDENTIFIER_URI, guards=[roles_accepted(*authorized_roles)], dependencies={'service': Provide(get_service)})
    async def get_user(id_: UUID, service: ServiceType) -> UserReadDTOType:  # TODO: add before/after hooks
        user = await service.get(id_)
        return user_read_dto.from_orm(user)


    @put(IDENTIFIER_URI, guards=[roles_accepted(*authorized_roles)], dependencies={'service': Provide(get_service)})
    async def update_user(id_: UUID, data: UserUpdateDTOType, service: ServiceType) -> UserReadDTOType:  # TODO: add before/after hooks
        user = await service.update(id_, data)
        return user_read_dto.from_orm(user)


    @delete(IDENTIFIER_URI, guards=[roles_accepted(*authorized_roles)], dependencies={'service': Provide(get_service)})
    async def delete_user(id_: UUID, service: ServiceType) -> None:  # TODO: add before/after hooks
        return await service.delete(id_)

    return Router(path=path_prefix, route_handlers=[get_user, update_user, delete_user])
