from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from advanced_alchemy.exceptions import RepositoryError
from litestar.contrib.jwt import JWTAuth, JWTCookieAuth
from litestar.dto import DTOData
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol
from litestar.security.session_auth import SessionAuth

from litestar_users.exceptions import TokenException, repository_exception_to_http_response, token_exception_handler
from litestar_users.route_handlers import (
    get_auth_handler,
    get_current_user_handler,
    get_password_reset_handler,
    get_registration_handler,
    get_role_management_handler,
    get_user_management_handler,
    get_verification_handler,
)
from litestar_users.schema import AuthenticationSchema, ForgotPasswordSchema, ResetPasswordSchema, UserRoleSchema
from litestar_users.user_handlers import (
    jwt_retrieve_user_handler,
    session_retrieve_user_handler,
)

__all__ = ["LitestarUsersPlugin"]


if TYPE_CHECKING:
    from click import Group
    from litestar import Router
    from litestar.config.app import AppConfig
    from litestar.handlers import HTTPRouteHandler
    from litestar.types import ExceptionHandlersMap

    from litestar_users.config import LitestarUsersConfig


class LitestarUsersPlugin(InitPluginProtocol, CLIPluginProtocol):
    """A Litestar extension for authentication, authorization and user management."""

    def __init__(self, config: LitestarUsersConfig) -> None:
        """Construct a LitestarUsers instance."""
        self._config = config

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        """Register routers, auth strategies etc on the Litestar app.

        Args:
            app_config: An instance of [AppConfig][litestar.config.AppConfig]
        """
        auth_backend = self._get_auth_backend()
        route_handlers = self._get_route_handlers(auth_backend)

        app_config = auth_backend.on_app_init(app_config)
        app_config.route_handlers.extend(route_handlers)

        exception_handlers: ExceptionHandlersMap = {
            RepositoryError: repository_exception_to_http_response,  # type: ignore[dict-item]
            TokenException: token_exception_handler,  # type: ignore[dict-item]
        }
        app_config.exception_handlers.update(exception_handlers)

        app_config.signature_namespace.update(
            {
                "ForgotPasswordSchema": ForgotPasswordSchema,
                "ResetPasswordSchema": ResetPasswordSchema,
                "AuthenticationSchema": AuthenticationSchema,
                "UserRoleSchema": UserRoleSchema,
                "UserServiceType": self._config.user_service_class,
                "BaseUserService": self._config.user_service_class,
                "SQLAUserT": self._config.user_model,
                "SQLARoleT": self._config.role_model,
                "role_create_dto": self._config.role_create_dto,
                "role_read_dto": self._config.role_read_dto,
                "role_update_dto": self._config.role_update_dto,
                "user_read_dto": self._config.user_read_dto,
                "user_update_dto": self._config.user_update_dto,
                "user_registration_dto": self._config.user_registration_dto,
                "DTOData": DTOData,
                "UserRegisterT": self._config.user_registration_dto.model_type,  # type: ignore[misc]
            }
        )
        app_config.state.update({"litestar_users_config": self._config})

        return app_config

    def on_cli_init(self, cli: Group) -> None:
        from litestar_users.cli import user_management_group

        cli.add_command(user_management_group)
        return super().on_cli_init(cli)

    def _get_auth_backend(self) -> JWTAuth | JWTCookieAuth | SessionAuth:
        if issubclass(self._config.auth_backend_class, SessionAuth):
            return self._config.auth_backend_class(
                retrieve_user_handler=session_retrieve_user_handler,  # type: ignore[arg-type]
                session_backend_config=self._config.session_backend_config,  # type: ignore
                exclude=self._config.auth_exclude_paths,
            )
        if issubclass(self._config.auth_backend_class, JWTAuth) or issubclass(
            self._config.auth_backend_class, JWTCookieAuth
        ):
            return self._config.auth_backend_class(
                retrieve_user_handler=jwt_retrieve_user_handler,  # type: ignore[arg-type]
                token_secret=self._config.secret,
                exclude=self._config.auth_exclude_paths,
            )
        raise ValueError("invalid auth backend")

    def _get_route_handlers(
        self, auth_backend: JWTAuth | JWTCookieAuth | SessionAuth
    ) -> Sequence[HTTPRouteHandler | Router]:
        """Parse the route handler configs to get Routers."""

        handlers: list[HTTPRouteHandler | Router] = []
        if self._config.auth_handler_config:
            handlers.append(
                get_auth_handler(
                    login_path=self._config.auth_handler_config.login_path,
                    logout_path=self._config.auth_handler_config.logout_path,
                    user_read_dto=self._config.user_read_dto,
                    auth_backend=auth_backend,
                    tags=self._config.auth_handler_config.tags,
                )
            )
        if self._config.current_user_handler_config:
            handlers.append(
                get_current_user_handler(
                    path=self._config.current_user_handler_config.path,
                    user_read_dto=self._config.user_read_dto,
                    user_update_dto=self._config.user_update_dto,
                    tags=self._config.current_user_handler_config.tags,
                )
            )
        if self._config.password_reset_handler_config:
            handlers.append(
                get_password_reset_handler(
                    forgot_path=self._config.password_reset_handler_config.forgot_path,
                    reset_path=self._config.password_reset_handler_config.reset_path,
                    tags=self._config.password_reset_handler_config.tags,
                )
            )
        if self._config.register_handler_config:
            handlers.append(
                get_registration_handler(
                    path=self._config.register_handler_config.path,
                    user_registration_dto=self._config.user_registration_dto,
                    user_read_dto=self._config.user_read_dto,
                    tags=self._config.register_handler_config.tags,
                )
            )
        if self._config.role_management_handler_config:
            handlers.append(
                get_role_management_handler(
                    path_prefix=self._config.role_management_handler_config.path_prefix,
                    assign_role_path=self._config.role_management_handler_config.assign_role_path,
                    revoke_role_path=self._config.role_management_handler_config.revoke_role_path,
                    guards=self._config.role_management_handler_config.guards,
                    opt=self._config.role_management_handler_config.opt,
                    role_create_dto=self._config.role_create_dto,  # type: ignore[arg-type]
                    role_read_dto=self._config.role_read_dto,  # type: ignore[arg-type]
                    role_update_dto=self._config.role_update_dto,  # type: ignore[arg-type]
                    user_read_dto=self._config.user_read_dto,
                    tags=self._config.role_management_handler_config.tags,
                )
            )
        if self._config.user_management_handler_config:
            handlers.append(
                get_user_management_handler(
                    path_prefix=self._config.user_management_handler_config.path_prefix,
                    guards=self._config.user_management_handler_config.guards,
                    opt=self._config.user_management_handler_config.opt,
                    user_read_dto=self._config.user_read_dto,
                    user_update_dto=self._config.user_update_dto,
                    tags=self._config.user_management_handler_config.tags,
                )
            )
        if self._config.verification_handler_config:
            handlers.append(
                get_verification_handler(
                    path=self._config.verification_handler_config.path,
                    user_read_dto=self._config.user_read_dto,
                    tags=self._config.verification_handler_config.tags,
                )
            )
        return handlers
