from typing import Any, Dict, Generic, Iterable, List, Literal, Optional, Type

from pydantic import BaseModel, SecretStr, root_validator
from starlite.middleware.session.base import BaseBackendConfig

from .adapter.sqlalchemy.mixins import RoleModelType, UserModelType
from .schema import (
    RoleCreateDTOType,
    RoleReadDTOType,
    RoleUpdateDTOType,
    UserCreateDTOType,
    UserReadDTOType,
    UserUpdateDTOType,
)
from .service import UserServiceType


class AuthHandlerConfig(BaseModel):
    """Configuration for user authentication route handlers.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.
    """

    login_path: str = "/login"
    """
    The path for the user authentication/login route.
    """
    logout_path: str = "/logout"
    """
    The path for the logout route.
    """


class CurrentUserHandlerConfig(BaseModel):
    """Configuration for the current-user route handler.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.
    """

    path: str = "/users/me"
    """
    The path to get or udpate the currently logged-in user.
    """


class PasswordResetHandlerConfig(BaseModel):
    """Configuration for the forgot-password and reset-password route handlers.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.
    """

    forgot_path: str = "/forgot-password"
    """
    The path for the forgot-password route.
    """
    reset_path: str = "/reset-password"
    """
    The path for the reset-password route.
    """


class RegisterHandlerConfig(BaseModel):
    """Configuration for the user registration route handler.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.
    """

    path: str = "/register"
    """
    The path for the registration/signup route.
    """


class RoleManagementHandlerConfig(BaseModel):
    """Configuration for the role management route handlers.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.
    """

    path_prefix: str = "/users/roles"
    """
    The prefix for the router path.
    """
    assign_role_path: str = "/assign"
    """
    The path for the role assignment router.
    """
    revoke_role_path: str = "/revoke"
    """
    The path for the role revokement router.
    """
    authorized_roles: Iterable[str] = ("administrator",)
    """
    An iterable of role names as strings that are authorized to manage roles.
    """


class UserManagementHandlerConfig(BaseModel):
    """Configuration for user management (read, update, delete) route handlers.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.

    Note:
    - These routes make use of Starlite `Guard`s to require authorization. Callers require admin or similar privileges.
    """

    path_prefix: str = "/users"
    """
    The prefix for the router path. By default, the path will be suffixed with `'/{id_:uuid}'`.
    """
    authorized_roles: Iterable[str] = ("administrator",)
    """
    An iterable of role names as strings that are authorized to manage other users.
    """


class VerificationHandlerConfig(BaseModel):
    """Configuration for the user verification route handler.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.
    """

    path: str = "/verify"
    """
    The path for the verification route.
    """


class StarliteUsersConfig(BaseModel, Generic[UserModelType]):
    """Configuration class for StarliteUsers."""

    class Config:
        arbitrary_types_allowed = True

    auth_exclude_paths: List[str] = ["/schema"]
    """
    Paths to be excluded from authentication checks.
    """
    auth_backend: Literal["session", "jwt", "jwt_cookie"]
    """
    The authentication backend to use by Starlite.
    """
    secret: SecretStr
    """
    Secret string for securely signing tokens.
    """
    session_backend_config: Optional[BaseBackendConfig] = None
    """
    Optional backend configuration for session based authentication.

    Notes:
        - Required if `auth_backend` is set to `session`.
    """
    user_model: Type[UserModelType]
    """
    A subclass of a `User` ORM model.
    """
    user_create_dto: Type[UserCreateDTOType]
    """
    A subclass of [BaseUserCreateDTO][starlite_users.schema.BaseUserCreateDTO].
    """
    user_read_dto: Type[UserReadDTOType]
    """
    A subclass of [BaseUserReadDTO][starlite_users.schema.BaseUserReadDTO].
    """
    user_update_dto: Type[UserUpdateDTOType]
    """
    A subclass of [BaseUserUpdateDTO][starlite_users.schema.BaseUserUpdateDTO].
    """
    role_model: Optional[Type[RoleModelType]]
    """
    A subclass of a `Role` ORM model.

    Notes:
        - Required if `role_management_handler_config` is set.
    """
    role_create_dto: Optional[Type[RoleCreateDTOType]]
    """
    A subclass of [BaseRoleCreateDTO][starlite_users.schema.BaseRoleCreateDTO].

    Notes:
        - Required if `role_management_handler_config` is set.
    """
    role_read_dto: Optional[Type[RoleReadDTOType]]
    """
    A subclass of [BaseRoleReadDTO][starlite_users.schema.BaseRoleReadDTO].

    Notes:
        - Required if `role_management_handler_config` is set.
    """
    role_update_dto: Optional[Type[RoleUpdateDTOType]]
    """
    A subclass of [BaseRoleUpdateDTO][starlite_users.schema.BaseRoleUpdateDTO].

    Notes:
        - Required if `role_management_handler_config` is set.
    """
    user_service_class: Type[UserServiceType]
    """
    A subclass of [BaseUserService][starlite_users.service.BaseUserService].
    """
    auth_handler_config: Optional[AuthHandlerConfig]
    """
    Optional instance of [AuthHandlerConfig][starlite_users.config.AuthHandlerConfig]. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    current_user_handler_config: Optional[CurrentUserHandlerConfig]
    """
    Optional current-user route handler configuration. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    password_reset_handler_config: Optional[PasswordResetHandlerConfig]
    """
    Optional password reset route handler configuration. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    register_handler_config: Optional[RegisterHandlerConfig]
    """
    Optional registration/signup route handler configuration. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    role_management_handler_config: Optional[RoleManagementHandlerConfig]
    """
    Optional role management route handler configuration. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    user_management_handler_config: Optional[UserManagementHandlerConfig]
    """
    Optional user management route handler configuration. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    verification_handler_config: Optional[VerificationHandlerConfig]
    """
    Optional user verification route handler configuration. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """

    @root_validator
    def validate_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the configuration.

        - A session backend must be configured if `auth_backend` is set to `'session'`.
        - At least one route handler must be configured.
        - `role_model`, `role_create_dto`, `role_read_dto` and `role_update_dto` are required fields if `role_management_handler_config` is configured.
        """
        if values.get("auth_backend") == "session" and not values.get("session_backend_config"):
            raise ValueError('session_backend_config must be set when auth_backend is set to "session"')
        if (
            values.get("auth_handler_config") is None
            and values.get("current_user_handler_config") is None
            and values.get("password_reset_handler_config") is None
            and values.get("register_handler_config") is None
            and values.get("role_management_handler_config") is None
            and values.get("user_management_handler_config") is None
            and values.get("verification_handler_config") is None
        ):
            raise ValueError("at least one route handler must be configured")
        if values.get("role_management_handler_config"):
            if values.get("role_model") is None:
                raise ValueError("role_model must be set when role_management_handler_config is set")
            if values.get("role_create_dto") is None:
                raise ValueError("role_create_dto must be set when role_management_handler_config is set")
            if values.get("role_read_dto") is None:
                raise ValueError("role_read_dto must be set when role_management_handler_config is set")
            if values.get("role_update_dto") is None:
                raise ValueError("role_update_dto must be set when role_management_handler_config is set")

        return values
