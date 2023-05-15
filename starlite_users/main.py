from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Sequence

from starlite_users.dependencies import get_service_dependency
from starlite_users.exceptions import (
    RepositoryException,
    TokenException,
    repository_exception_handler,
    token_exception_handler,
)
from starlite_users.route_handlers import (
    get_auth_handler,
    get_current_user_handler,
    get_password_reset_handler,
    get_registration_handler,
    get_role_management_handler,
    get_user_management_handler,
    get_verification_handler,
)

__all__ = ["StarliteUsers"]


if TYPE_CHECKING:
    from starlite import HTTPRouteHandler, Request, Response, Router
    from starlite.config import AppConfig
    from starlite.contrib.jwt import JWTAuth, JWTCookieAuth
    from starlite.security.session_auth import SessionAuth

    from starlite_users.config import StarliteUsersConfig


class StarliteUsers:
    """A Starlite extension for authentication, authorization and user management."""

    def __init__(self, config: "StarliteUsersConfig") -> None:
        """Construct a StarliteUsers instance."""
        self._config = config

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Register routers, auth strategies etc on the Starlite app.

        Args:
            app_config: An instance of [AppConfig][starlite.config.AppConfig]
        """
        auth_backend = self._config.auth_config
        route_handlers = self._get_route_handlers(auth_backend)

        app_config = auth_backend.on_app_init(app_config)
        app_config.route_handlers.extend(route_handlers)

        exception_handlers: dict[type[Exception], Callable[[Request, Any], Response]] = {
            TokenException: token_exception_handler,
            RepositoryException: repository_exception_handler,
        }
        app_config.exception_handlers.update(exception_handlers)  # type: ignore[arg-type]

        return app_config

    def _get_route_handlers(
        self, auth_backend: JWTAuth | JWTCookieAuth | SessionAuth
    ) -> Sequence[HTTPRouteHandler | Router]:
        """Parse the route handler configs to get Routers."""

        handlers: list[HTTPRouteHandler | Router] = []
        service_dependency_provider = get_service_dependency(
            user_model=self._config.user_model,
            role_model=self._config.role_model,
            user_service_class=self._config.user_service_class,
            user_repository_class=self._config.user_repository_class,
            secret=self._config.secret,
            hash_schemes=self._config.hash_schemes,
        )
        if self._config.auth_handler_config:
            handlers.append(
                get_auth_handler(
                    login_path=self._config.auth_handler_config.login_path,
                    logout_path=self._config.auth_handler_config.logout_path,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=service_dependency_provider,
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
                    service_dependency=service_dependency_provider,
                    tags=self._config.current_user_handler_config.tags,
                )
            )
        if self._config.password_reset_handler_config:
            handlers.append(
                get_password_reset_handler(
                    forgot_path=self._config.password_reset_handler_config.forgot_path,
                    reset_path=self._config.password_reset_handler_config.reset_path,
                    service_dependency=service_dependency_provider,
                    tags=self._config.password_reset_handler_config.tags,
                )
            )
        if self._config.register_handler_config:
            handlers.append(
                get_registration_handler(
                    path=self._config.register_handler_config.path,
                    user_create_dto=self._config.user_create_dto,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=service_dependency_provider,
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
                    role_create_dto=self._config.role_create_dto,
                    role_read_dto=self._config.role_read_dto,
                    role_update_dto=self._config.role_update_dto,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=service_dependency_provider,
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
                    service_dependency=service_dependency_provider,
                    tags=self._config.user_management_handler_config.tags,
                )
            )
        if self._config.verification_handler_config:
            handlers.append(
                get_verification_handler(
                    path=self._config.verification_handler_config.path,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=service_dependency_provider,
                    tags=self._config.verification_handler_config.tags,
                )
            )
        return handlers
