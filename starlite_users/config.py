from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Literal

from pydantic import SecretStr
from starlite.contrib.jwt import JWTAuth, JWTCookieAuth
from starlite.exceptions import ImproperlyConfiguredException
from starlite.security.session_auth import SessionAuth

from starlite_users.adapter.sqlalchemy.mixins import (
    SQLAlchemyRoleMixin,
    UserModelType,
)
from starlite_users.adapter.sqlalchemy.repository import SQLAlchemyUserRepository
from starlite_users.schema import (
    BaseRoleCreateDTO,
    BaseRoleReadDTO,
    BaseRoleUpdateDTO,
    BaseUserCreateDTO,
    BaseUserReadDTO,
    BaseUserUpdateDTO,
)
from starlite_users.user_handlers import (
    get_jwt_retrieve_user_handler,
    get_session_retrieve_user_handler,
)

__all__ = [
    "AuthHandlerConfig",
    "CurrentUserHandlerConfig",
    "PasswordResetHandlerConfig",
    "RegisterHandlerConfig",
    "RoleManagementHandlerConfig",
    "StarliteUsersConfig",
    "UserManagementHandlerConfig",
    "VerificationHandlerConfig",
]

if TYPE_CHECKING:
    from starlite.middleware.session.base import BaseBackendConfig
    from starlite.types import Guard

    from starlite_users.service import BaseUserService


@dataclass
class AuthHandlerConfig:
    """Configuration for user authentication route handlers.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.
    """

    login_path: str = "/login"
    """The path for the user authentication/login route."""
    logout_path: str = "/logout"
    """The path for the logout route."""
    tags: list[str] | None = None
    """A list of string tags to append to the schema of the route handler(s)."""


@dataclass
class CurrentUserHandlerConfig:
    """Configuration for the current-user route handler.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.
    """

    path: str = "/users/me"
    """The path to get or update the currently logged-in user."""
    tags: list[str] | None = None
    """A list of string tags to append to the schema of the route handler(s)."""


@dataclass
class PasswordResetHandlerConfig:
    """Configuration for the forgot-password and reset-password route handlers.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.
    """

    forgot_path: str = "/forgot-password"
    """The path for the forgot-password route."""
    reset_path: str = "/reset-password"
    """The path for the reset-password route."""
    tags: list[str] | None = None
    """A list of string tags to append to the schema of the route handler(s)."""


@dataclass
class RegisterHandlerConfig:
    """Configuration for the user registration route handler.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.
    """

    path: str = "/register"
    """The path for the registration/signup route."""
    tags: list[str] | None = None
    """A list of string tags to append to the schema of the route handler(s)."""


@dataclass
class RoleManagementHandlerConfig:
    """Configuration for the role management route handlers.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.
    """

    path_prefix: str = "/users/roles"
    """The prefix for the router path."""
    assign_role_path: str = "/assign"
    """The path for the role assignment router."""
    revoke_role_path: str = "/revoke"
    """The path for the role revokement router."""
    guards: list[Guard] = field(default_factory=list)
    """A list of callable [Guards][starlite.types.Guard] that determines who is authorized to manage roles."""
    opt: dict[str, Any] = field(default_factory=dict)
    """Optional route handler [opts][starlite.controller.Controller.opt] to provide additional context to Guards."""
    tags: list[str] | None = None
    """A list of string tags to append to the schema of the route handler(s)."""


@dataclass
class UserManagementHandlerConfig:
    """Configuration for user management (read, update, delete) route handlers.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.

    Note:
    - These routes make use of Starlite `Guard`s to require authorization. Callers require admin or similar privileges.
    """

    path_prefix: str = "/users"
    """The prefix for the router path.

    By default, the path will be suffixed with `'/{id_:uuid}'`.
    """
    guards: list[Guard] = field(default_factory=list)
    """A list of callable [Guards][starlite.types.Guard] that determines who is authorized to manage other users."""
    opt: dict[str, Any] = field(default_factory=dict)
    """Optional route handler [opts][starlite.controller.Controller.opt] to provide additional context to Guards."""
    tags: list[str] | None = None
    """A list of string tags to append to the schema of the route handler(s)."""


@dataclass
class VerificationHandlerConfig:
    """Configuration for the user verification route handler.

    Passing an instance to `StarliteUsersConfig` will automatically take care of handler registration on the app.
    """

    path: str = "/verify"
    """The path for the verification route."""
    tags: list[str] | None = None
    """A list of string tags to append to the schema of the route handler(s)."""


@dataclass
class StarliteUsersConfig(Generic[UserModelType]):
    """Configuration class for StarliteUsers."""

    auth_backend: Literal["session", "jwt", "jwt_cookie"]
    """The authentication backend to use by Starlite."""
    secret: SecretStr
    """Secret string for securely signing tokens."""
    user_model: type[UserModelType]
    """A subclass of a `User` ORM model."""
    user_service_class: type[BaseUserService]
    """A subclass of [BaseUserService][starlite_users.service.BaseUserService]."""
    user_create_dto: type[BaseUserCreateDTO] = BaseUserCreateDTO
    """A subclass of [BaseUserCreateDTO][starlite_users.schema.BaseUserCreateDTO]."""
    user_read_dto: type[BaseUserReadDTO] = BaseUserReadDTO
    """A subclass of [BaseUserReadDTO][starlite_users.schema.BaseUserReadDTO]."""
    user_update_dto: type[BaseUserUpdateDTO] = BaseUserUpdateDTO
    """A subclass of [BaseUserUpdateDTO][starlite_users.schema.BaseUserUpdateDTO]."""
    user_repository_class: type[SQLAlchemyUserRepository] = SQLAlchemyUserRepository
    """The user repository class to use."""
    auth_exclude_paths: list[str] = field(default_factory=lambda: ["/schema"])
    """Paths to be excluded from authentication checks."""
    hash_schemes: list[str] = field(default_factory=lambda: ["argon2"])
    """Schemes to use for password encryption.

    Defaults to `["argon2"]`
    """
    session_backend_config: BaseBackendConfig | None = None
    """Optional backend configuration for session based authentication.

    Notes:
        - Required if `auth_backend` is set to `session`.
    """
    role_model: type[SQLAlchemyRoleMixin] = SQLAlchemyRoleMixin
    """A subclass of a `Role` ORM model.

    Notes:
        - Required if `role_management_handler_config` is set.
    """
    role_create_dto: type[BaseRoleCreateDTO] = BaseRoleCreateDTO
    """A subclass of [BaseRoleCreateDTO][starlite_users.schema.BaseRoleCreateDTO].

    Notes:
        - Required if `role_management_handler_config` is set.
    """
    role_read_dto: type[BaseRoleReadDTO] = BaseRoleReadDTO
    """A subclass of [BaseRoleReadDTO][starlite_users.schema.BaseRoleReadDTO].

    Notes:
        - Required if `role_management_handler_config` is set.
    """
    role_update_dto: type[BaseRoleUpdateDTO] = BaseRoleUpdateDTO
    """A subclass of [BaseRoleUpdateDTO][starlite_users.schema.BaseRoleUpdateDTO].

    Notes:
        - Required if `role_management_handler_config` is set.
    """
    auth_handler_config: AuthHandlerConfig | None = None
    """Optional instance of [AuthHandlerConfig][starlite_users.config.AuthHandlerConfig]. If set, registers the route
    handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    current_user_handler_config: CurrentUserHandlerConfig | None = None
    """Optional current-user route handler configuration. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    password_reset_handler_config: PasswordResetHandlerConfig | None = None
    """Optional password reset route handler configuration. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    register_handler_config: RegisterHandlerConfig | None = None
    """Optional registration/signup route handler configuration. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    role_management_handler_config: RoleManagementHandlerConfig | None = None
    """Optional role management route handler configuration. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    user_management_handler_config: UserManagementHandlerConfig | None = None
    """Optional user management route handler configuration. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    verification_handler_config: VerificationHandlerConfig | None = None
    """Optional user verification route handler configuration. If set, registers the route handler(s) on the app.

    Note:
        - At least one route handler config must be set.
    """
    _auth_config: JWTAuth | JWTCookieAuth | SessionAuth | None = None

    def __post_init__(self) -> None:
        """Validate the configuration.

        - A session backend must be configured if `auth_backend` is set to `'session'`.
        - At least one route handler must be configured.
        - `role_model`, `role_create_dto`, `role_read_dto` and `role_update_dto` are required fields if `role_management_handler_config` is configured.
        """
        if self.auth_backend == "session" and not self.session_backend_config:
            raise ImproperlyConfiguredException(
                'session_backend_config must be set when auth_backend is set to "session"'
            )
        handler_configs = [
            "auth_handler_config",
            "current_user_handler_config",
            "password_reset_handler_config",
            "register_handler_config",
            "role_management_handler_config",
            "user_management_handler_config",
            "verification_handler_config",
        ]
        if isinstance(self.secret, str):
            self.secret = SecretStr(self.secret)
        if len(self.secret) not in [16, 24, 32]:
            raise ImproperlyConfiguredException("secret must be 16, 24 or 32 characters")
        if all(getattr(self, config) is None for config in handler_configs):
            raise ImproperlyConfiguredException("at least one route handler must be configured")
        if self.role_management_handler_config and self.role_model is SQLAlchemyRoleMixin:
            raise ImproperlyConfiguredException("role_model must be set when role_management_handler_config is set")

        self._auth_config = self._get_auth_config()

    @property
    def auth_config(self) -> JWTAuth | JWTCookieAuth | SessionAuth:
        return self._auth_config or self._get_auth_config()

    def _get_auth_config(self) -> JWTAuth | JWTCookieAuth | SessionAuth:
        if self.auth_backend == "session":
            return SessionAuth(
                retrieve_user_handler=get_session_retrieve_user_handler(
                    user_model=self.user_model,
                    role_model=self.role_model,
                    user_repository_class=self.user_repository_class,
                ),
                session_backend_config=self.session_backend_config,  # type: ignore
                exclude=self.auth_exclude_paths,
            )
        if self.auth_backend == "jwt":
            return JWTAuth(
                retrieve_user_handler=get_jwt_retrieve_user_handler(
                    user_model=self.user_model,
                    role_model=self.role_model,
                    user_repository_class=self.user_repository_class,
                ),
                token_secret=self.secret.get_secret_value(),
                exclude=self.auth_exclude_paths,
            )

        return JWTCookieAuth(
            retrieve_user_handler=get_jwt_retrieve_user_handler(
                user_model=self.user_model,
                role_model=self.role_model,
                user_repository_class=self.user_repository_class,
            ),
            token_secret=self.secret.get_secret_value(),
            exclude=self.auth_exclude_paths,
        )
