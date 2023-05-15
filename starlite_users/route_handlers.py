from typing import TYPE_CHECKING, Any, Callable, Dict, List, Literal, Optional, Type, Union
from uuid import UUID

from starlite import (
    HTTPRouteHandler,
    Provide,
    Request,
    Response,
    Router,
    delete,
    get,
    patch,
    post,
    put,
)
from starlite.contrib.jwt import JWTAuth, JWTCookieAuth
from starlite.exceptions import ImproperlyConfiguredException, NotAuthorizedException, PermissionDeniedException
from starlite.security.session_auth.auth import SessionAuth

from starlite_users.adapter.sqlalchemy.mixins import UserModelType
from starlite_users.schema import (
    ForgotPasswordSchema,
    ResetPasswordSchema,
    RoleCreateDTOType,
    RoleReadDTOType,
    RoleUpdateDTOType,
    UserAuthSchema,
    UserCreateDTOType,
    UserReadDTOType,
    UserRoleSchema,
    UserUpdateDTOType,
)
from starlite_users.service import BaseUserService

__all__ = [
    "get_auth_handler",
    "get_current_user_handler",
    "get_password_reset_handler",
    "get_registration_handler",
    "get_role_management_handler",
    "get_user_management_handler",
    "get_verification_handler",
]


if TYPE_CHECKING:
    from starlite.types import Guard

IDENTIFIER_URI = "/{id_:uuid}"  # TODO: define via config


def get_registration_handler(
    path: str,
    user_create_dto: Type[UserCreateDTOType],
    user_read_dto: Type[UserReadDTOType],
    service_dependency: Callable,
    tags: Optional[List[str]] = None,
) -> HTTPRouteHandler:
    """Get registration route handlers.

    Args:
        path: The path for the router.
        user_create_dto: A subclass of [BaseUserCreateDTO][starlite_users.schema.BaseUserCreateDTO]
        user_read_dto: A subclass of [BaseUserReadDTO][starlite_users.schema.BaseUserReadDTO]
        service_dependency: Callable to provide a `UserService` instance.
        tags: A list of string tags to append to the schema of the route handler.
    """

    @post(path, dependencies={"service": Provide(service_dependency)}, exclude_from_auth=True, tags=tags)
    async def register(data: user_create_dto, service: BaseUserService) -> user_read_dto:  # type: ignore[valid-type]
        """Register a new user."""

        user = await service.register(data)
        return user_read_dto.from_orm(user)

    return register


def get_verification_handler(
    path: str, user_read_dto: Type[UserReadDTOType], service_dependency: Callable, tags: Optional[List[str]] = None
) -> HTTPRouteHandler:
    """Get verification route handlers.

    Args:
        path: The path for the router.
        user_read_dto: A subclass of [BaseUserReadDTO][starlite_users.schema.BaseUserReadDTO]
        service_dependency: Callable to provide a `UserService` instance.
        tags: A list of string tags to append to the schema of the route handler.
    """

    @post(path, dependencies={"service": Provide(service_dependency)}, exclude_from_auth=True, tags=tags)
    async def verify(token: str, service: BaseUserService) -> user_read_dto:  # type: ignore[valid-type]
        """Verify a user with a given JWT."""

        user = await service.verify(token)
        return user_read_dto.from_orm(user)

    return verify


def get_auth_handler(
    login_path: str,
    logout_path: str,
    user_read_dto: Type[UserReadDTOType],
    service_dependency: Callable,
    auth_backend: Union[JWTAuth, JWTCookieAuth, SessionAuth],
    tags: Optional[List[str]] = None,
) -> Router:
    """Get authentication/login route handlers.

    Args:
        login_path: The path for the login router.
        logout_path: The path for the logout router.
        user_read_dto: A subclass of [BaseUserReadDTO][starlite_users.schema.BaseUserReadDTO]
        service_dependency: Callable to provide a `UserService` instance.
        auth_backend: A Starlite authentication backend.
        tags: A list of string tags to append to the schema of the route handlers.
    """

    @post(login_path, dependencies={"service": Provide(service_dependency)}, exclude_from_auth=True, tags=tags)
    async def login_session(data: UserAuthSchema, service: BaseUserService, request: Request) -> user_read_dto:  # type: ignore[valid-type]
        """Authenticate a user."""
        if not isinstance(auth_backend, SessionAuth):
            raise ImproperlyConfiguredException("session login can only be used with SesssionAuth")

        user = await service.authenticate(data)
        if user is None:
            request.clear_session()
            raise NotAuthorizedException(detail="login failed, invalid input")

        if user.is_verified is False:
            raise PermissionDeniedException(detail="not verified")

        request.set_session({"user_id": user.id})
        return user_read_dto.from_orm(user)

    @post(login_path, dependencies={"service": Provide(service_dependency)}, exclude_from_auth=True, tags=tags)
    async def login_jwt(data: UserAuthSchema, service: BaseUserService) -> Response[user_read_dto]:  # type: ignore
        """Authenticate a user."""

        if not isinstance(auth_backend, (JWTAuth, JWTCookieAuth)):
            raise ImproperlyConfiguredException("jwt login can only be used with JWTAuth")

        user = await service.authenticate(data)
        if user is None:
            raise NotAuthorizedException(detail="login failed, invalid input")

        if user.is_verified is False:
            raise PermissionDeniedException(detail="not verified")

        user_dto = user_read_dto.from_orm(user)
        return auth_backend.login(identifier=str(user.id), response_body=user_dto)

    @post(logout_path, tags=tags)
    async def logout(request: Request) -> None:
        """Log an authenticated user out."""
        request.clear_session()

    route_handlers = []
    if isinstance(auth_backend, SessionAuth):
        route_handlers.extend([login_session, logout])
    else:
        route_handlers.append(login_jwt)

    return Router(path="/", route_handlers=route_handlers)  # type: ignore[arg-type]


def get_current_user_handler(
    path: str,
    user_read_dto: Type[UserReadDTOType],
    user_update_dto: Type[UserUpdateDTOType],
    service_dependency: Callable,
    tags: Optional[List[str]] = None,
) -> Router:
    """Get current-user route handlers.

    Args:
        path: The path for the router.
        user_read_dto: A subclass of [BaseUserReadDTO][starlite_users.schema.BaseUserReadDTO]
        user_update_dto: A subclass of [BaseUserUpdateDTO][starlite_users.schema.BaseUserUpdateDTO]
        service_dependency: Callable to provide a `UserService` instance.
        tags: A list of string tags to append to the schema of the route handlers.
    """

    @get(path, tags=tags)
    async def get_current_user(request: Request[UserModelType, Dict[Literal["user_id"], str]]) -> user_read_dto:  # type: ignore[valid-type]
        """Get current user info."""

        return user_read_dto.from_orm(request.user)

    @put(path, dependencies={"service": Provide(service_dependency)}, tags=tags)
    async def update_current_user(
        data: user_update_dto,  # type: ignore[valid-type]
        request: Request[UserModelType, Dict[Literal["user_id"], str]],
        service: BaseUserService,
    ) -> user_read_dto:  # type: ignore[valid-type]
        """Update the current user."""

        updated_user = await service.update_user(id_=request.user.id, data=data)
        return user_read_dto.from_orm(updated_user)

    return Router(path="/", route_handlers=[get_current_user, update_current_user])


def get_password_reset_handler(
    forgot_path: str, reset_path: str, service_dependency: Callable, tags: Optional[List[str]] = None
) -> Router:
    """Get forgot-password and reset-password route handlers.

    Args:
        forgot_path: The path for the forgot-password router.
        reset_path: The path for the reset-password router.
        service_dependency: Callable to provide a `UserService` instance.
        tags: A list of string tags to append to the schema of the route handlers.
    """

    @post(forgot_path, dependencies={"service": Provide(service_dependency)}, exclude_from_auth=True, tags=tags)
    async def forgot_password(data: ForgotPasswordSchema, service: BaseUserService) -> None:
        await service.initiate_password_reset(data.email)
        return

    @post(reset_path, dependencies={"service": Provide(service_dependency)}, exclude_from_auth=True, tags=tags)
    async def reset_password(data: ResetPasswordSchema, service: BaseUserService) -> None:
        await service.reset_password(data.token, data.password)
        return

    return Router(path="/", route_handlers=[forgot_password, reset_password])


def get_user_management_handler(
    path_prefix: str,
    guards: List["Guard"],
    opt: Dict[str, Any],
    user_read_dto: Type[UserReadDTOType],
    user_update_dto: Type[UserUpdateDTOType],
    service_dependency: Callable,
    tags: Optional[List[str]] = None,
) -> Router:
    """Get user management route handlers.

    Note:
        Routes are guarded by role authorization.

    Args:
        path_prefix: The path prefix for the routers.
        guards: List of Guard callables to determine who is authorized to manage users.
        opt: Optional route handler 'opts' to provide additional context to Guards.
        user_read_dto: A subclass of [BaseUserReadDTO][starlite_users.schema.BaseUserReadDTO]
        user_update_dto: A subclass of [BaseUserUpdateDTO][starlite_users.schema.BaseUserUpdateDTO]
        service_dependency: Callable to provide a `UserService` instance.
        tags: A list of string tags to append to the schema of the route handlers.
    """

    @get(IDENTIFIER_URI, guards=guards, opt=opt, dependencies={"service": Provide(service_dependency)}, tags=tags)
    async def get_user(id_: UUID, service: BaseUserService) -> user_read_dto:  # type: ignore[valid-type]
        """Get a user by id."""

        user = await service.get_user(id_)
        return user_read_dto.from_orm(user)

    @put(IDENTIFIER_URI, guards=guards, opt=opt, dependencies={"service": Provide(service_dependency)}, tags=tags)
    async def update_user(
        id_: UUID, data: user_update_dto, service: BaseUserService  # type: ignore[valid-type]
    ) -> user_read_dto:  # type: ignore[valid-type]
        """Update a user's attributes."""

        user = await service.update_user(id_, data)
        return user_read_dto.from_orm(user)

    @delete(IDENTIFIER_URI, guards=guards, opt=opt, dependencies={"service": Provide(service_dependency)}, tags=tags)
    async def delete_user(id_: UUID, service: BaseUserService) -> None:
        """Delete a user from the database."""

        return await service.delete_user(id_)

    return Router(path=path_prefix, route_handlers=[get_user, update_user, delete_user])


def get_role_management_handler(
    path_prefix: str,
    assign_role_path: str,
    revoke_role_path: str,
    guards: List["Guard"],
    opt: Dict[str, Any],
    role_create_dto: Type[RoleCreateDTOType],
    role_read_dto: Type[RoleReadDTOType],
    role_update_dto: Type[RoleUpdateDTOType],
    user_read_dto: Type[UserReadDTOType],
    service_dependency: Callable,
    tags: Optional[List[str]] = None,
) -> Router:
    """Get role management route handlers.

    Note:
        Routes are guarded by role authorization.

    Args:
        path_prefix: The path prefix for the routers.
        assign_role_path: The path for the role assignment router.
        revoke_role_path: The path for the role revokement router.
        guards: List of Guard callables to determine who is authorized to manage roles.
        opt: Optional route handler 'opts' to provide additional context to Guards.
        role_create_dto: A subclass of [BaseRoleCreateDTO][starlite_users.schema.BaseRoleCreateDTO]
        role_read_dto: A subclass of [BaseRoleReadDTO][starlite_users.schema.BaseRoleReadDTO]
        role_update_dto: A subclass of [BaseRoleUpdateDTO][starlite_users.schema.BaseRoleUpdateDTO]
        user_read_dto: A subclass of [BaseUserReadDTO][starlite_users.schema.BaseUserReadDTO]
        service_dependency: Callable to provide a `UserService` instance.
        tags: A list of string tags to append to the schema of the route handlers.
    """

    @post(guards=guards, opt=opt, dependencies={"service": Provide(service_dependency)}, tags=tags)
    async def create_role(data: role_create_dto, service: BaseUserService) -> role_read_dto:  # type: ignore[valid-type]
        """Create a new role."""
        role = await service.add_role(data)
        return role_read_dto.from_orm(role)

    @put(IDENTIFIER_URI, guards=guards, opt=opt, dependencies={"service": Provide(service_dependency)}, tags=tags)
    async def update_role(id_: UUID, data: role_update_dto, service: BaseUserService) -> role_read_dto:  # type: ignore[valid-type]
        """Update a role in the database."""

        role = await service.update_role(id_, data)
        return role_read_dto.from_orm(role)

    @delete(IDENTIFIER_URI, guards=guards, opt=opt, dependencies={"service": Provide(service_dependency)}, tags=tags)
    async def delete_role(id_: UUID, service: BaseUserService) -> None:
        """Delete a role from the database."""

        return await service.delete_role(id_)

    @patch(
        path=assign_role_path, guards=guards, opt=opt, dependencies={"service": Provide(service_dependency)}, tags=tags
    )
    async def assign_role_to_user(data: UserRoleSchema, service: BaseUserService) -> user_read_dto:  # type: ignore[valid-type]
        """Assign a role to a user."""

        user = await service.assign_role_to_user(data.user_id, data.role_id)
        return user_read_dto.from_orm(user)

    @patch(
        path=revoke_role_path, guards=guards, opt=opt, dependencies={"service": Provide(service_dependency)}, tags=tags
    )
    async def revoke_role_from_user(data: UserRoleSchema, service: BaseUserService) -> user_read_dto:  # type: ignore[valid-type]
        """Revoke a role from a user."""

        user = await service.revoke_role_from_user(data.user_id, data.role_id)
        return user_read_dto.from_orm(user)

    return Router(
        path_prefix, route_handlers=[create_role, assign_role_to_user, revoke_role_from_user, update_role, delete_role]
    )
