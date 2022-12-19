from typing import Callable, Dict, Literal, Optional, Tuple, Type, Union
from uuid import UUID

from starlite import (
    HTTPRouteHandler,
    Provide,
    Request,
    Response,
    Router,
    delete,
    get,
    post,
    put,
)
from starlite.contrib.jwt import JWTAuth, JWTCookieAuth
from starlite.exceptions import NotAuthorizedException
from starlite.security.session_auth.auth import SessionAuth

from .adapter.sqlalchemy.models import UserModelType
from .guards import roles_accepted
from .schema import (
    ForgotPasswordSchema,
    ResetPasswordSchema,
    UserAuthSchema,
    UserCreateDTOType,
    UserReadDTOType,
    UserUpdateDTOType,
)
from .service import UserServiceType

IDENTIFIER_URI = "/{id_:uuid}"  # TODO: define via config


def get_registration_handler(
    path: str, user_read_dto: Type[UserReadDTOType], service_dependency: Callable
) -> HTTPRouteHandler:
    """Factory to get registration route handlers.

    Args:
        path: The path for the router.
        user_read_dto: A subclass of [UserReadDTO][starlite_users.schema.UserReadDTO]
        service_dependency: Callable to provide a `UserService` instance.
    """

    @post(path, dependencies={"service": Provide(service_dependency)})
    async def register(data: UserCreateDTOType, service: UserServiceType) -> UserReadDTOType:
        """Register a new user."""

        user = await service.register(data)
        return user_read_dto.from_orm(user)

    return register


def get_verification_handler(
    path: str, user_read_dto: Type[UserReadDTOType], service_dependency: Callable
) -> HTTPRouteHandler:
    """Factory to get verification route handlers.

    Args:
        path: The path for the router.
        user_read_dto: A subclass of [UserReadDTO][starlite_users.schema.UserReadDTO]
        service_dependency: Callable to provide a `UserService` instance.
    """

    @post(path, dependencies={"service": Provide(service_dependency)})
    async def verify(token: str, service: UserServiceType) -> None:
        """Verify a user with a give JWT."""

        user = await service.verify(token)
        return user_read_dto.from_orm(user)

    return verify


def get_auth_handler(
    login_path: str,
    logout_path: str,
    user_read_dto: Type[UserReadDTOType],
    service_dependency: Callable,
    auth_backend: Union[JWTAuth, JWTCookieAuth, SessionAuth],
) -> Router:
    """Factory to get authentication/login route handlers.

    Args:
        login_path: The path for the login router.
        logout_path: The path for the logout router.
        user_read_dto: A subclass of [UserReadDTO][starlite_users.schema.UserReadDTO]
        service_dependency: Callable to provide a `UserService` instance.
    """

    @post(login_path, dependencies={"service": Provide(service_dependency)})
    async def login(data: UserAuthSchema, service: UserServiceType, request: Request) -> Response:
        """Authenticate a user."""

        user = await service.authenticate(data)
        if user is None:
            request.clear_session()
            raise NotAuthorizedException()

        user_dto = user_read_dto.from_orm(user)

        if isinstance(auth_backend, JWTAuth) or isinstance(auth_backend, JWTCookieAuth):
            response = auth_backend.login(identifier=str(user.id), response_body=user_dto)
        elif isinstance(auth_backend, SessionAuth):
            request.set_session({"user_id": user.id})  # TODO: move and make configurable
            response = Response(status_code=201, content=user_dto)

        return response

    @post(logout_path)
    async def logout(request: Request) -> None:
        """Log an authenticated user out."""
        request.clear_session()

    route_handlers = [login]
    if isinstance(auth_backend, SessionAuth):
        route_handlers.append(logout)

    return Router(path="/", route_handlers=route_handlers)


def get_current_user_handler(path: str, user_read_dto: Type[UserReadDTOType], service_dependency: Callable) -> Router:
    """Factory to get current-user route handlers.

    Args:
        path: The path for the router.
        user_read_dto: A subclass of [UserReadDTO][starlite_users.schema.UserReadDTO]
        service_dependency: Callable to provide a `UserService` instance.
    """

    @get(path)
    async def get_current_user(request: Request[UserModelType, Dict[Literal["user_id"], str]]) -> UserReadDTOType:
        """Get current user info."""

        return user_read_dto.from_orm(request.user)

    @put(path, dependencies={"service": Provide(service_dependency)})
    async def update_current_user(
        data: UserUpdateDTOType,
        request: Request[UserModelType, Dict[Literal["user_id"], str]],
        service: UserServiceType,
    ) -> Optional[UserReadDTOType]:
        """Update the current user."""

        updated_user = await service.update(id_=request.user.id, data=data)
        return user_read_dto.from_orm(updated_user)

    return Router(path="/", route_handlers=[get_current_user, update_current_user])


def get_password_reset_handler(forgot_path: str, reset_path: str, service_dependency: Callable) -> Router:
    """Factory to get forgot-password and reset-password route handlers.

    Args:
        forgot_path: The path for the forgot-password router.
        reset_path: The path for the reset-password router.
        service_dependency: Callable to provide a `UserService` instance.
    """

    @post(forgot_path, dependencies={"service": Provide(service_dependency)})
    async def forgot_password(data: ForgotPasswordSchema, service: UserServiceType) -> None:
        await service.initiate_password_reset(data.email)
        return

    @post(reset_path, dependencies={"service": Provide(service_dependency)})
    async def reset_password(data: ResetPasswordSchema, service: UserServiceType) -> None:
        await service.reset_password(data.token, data.password)
        return

    return Router(path="/", route_handlers=[forgot_password, reset_password])


def get_user_management_handler(
    path_prefix: str,
    authorized_roles: Tuple[str],
    user_read_dto: Type[UserReadDTOType],
    service_dependency: Callable,
) -> Router:
    """Factory to get user management route handlers.

    Note:
        Users require authorized priveleges.

    Args:
        path_prefix: The path prefix for the routers.
        authorized_roles: Role names that are authorized to manage users.
        user_read_dto: A subclass of [UserReadDTO][starlite_users.schema.UserReadDTO]
        service_dependency: Callable to provide a `UserService` instance.
    """

    @get(
        IDENTIFIER_URI,
        guards=[roles_accepted(*authorized_roles)],
        dependencies={"service": Provide(service_dependency)},
    )
    async def get_user(id_: UUID, service: UserServiceType) -> UserReadDTOType:  # TODO: add before/after hooks
        """Get a user by id."""

        user = await service.get(id_)
        return user_read_dto.from_orm(user)

    @put(
        IDENTIFIER_URI,
        guards=[roles_accepted(*authorized_roles)],
        dependencies={"service": Provide(service_dependency)},
    )
    async def update_user(
        id_: UUID, data: UserUpdateDTOType, service: UserServiceType
    ) -> UserReadDTOType:  # TODO: add before/after hooks
        """Update a user's attributes."""

        user = await service.update(id_, data)
        return user_read_dto.from_orm(user)

    @delete(
        IDENTIFIER_URI,
        guards=[roles_accepted(*authorized_roles)],
        dependencies={"service": Provide(service_dependency)},
    )
    async def delete_user(id_: UUID, service: UserServiceType) -> None:  # TODO: add before/after hooks
        """Delete a user from the database."""

        return await service.delete(id_)

    return Router(path=path_prefix, route_handlers=[get_user, update_user, delete_user])
