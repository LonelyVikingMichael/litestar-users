from typing import TYPE_CHECKING, List, Union

from starlite import HTTPRouteHandler, OpenAPIConfig, Router
from starlite.security.session_auth import SessionAuth

from .config import StarliteUsersConfig
from .route_handlers import (
    get_auth_handler,
    get_current_user_handler,
    get_password_reset_handler,
    get_registration_handler,
    get_user_management_handler,
    get_verification_handler,
)
from .service import get_retrieve_user_handler, get_service_dependency

if TYPE_CHECKING:
    from starlite.config import AppConfig

EXCLUDE_AUTH_HANDLERS = (
    "login",
    "register",
    "verify",
    "forgot_password",
    "reset_password",
)


class StarliteUsersPlugin:
    """A Plugin for authentication, authorization and user management."""

    def __init__(self, config: StarliteUsersConfig) -> None:
        self._config = config

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Register routers, auth strategies etc on the Starlite app.

        Args:
            app_config: An instance of [AppConfig][starlite.config.AppConfig]
        """
        _auth_exclude_paths = {*self._config.auth_exclude_paths}

        route_handlers = self._get_route_handlers()
        for router in route_handlers:
            if isinstance(router, Router):
                for route in router.routes:
                    if any(name in EXCLUDE_AUTH_HANDLERS for name in route.handler_names):
                        _auth_exclude_paths.add(route.path)
            if isinstance(router, HTTPRouteHandler) and router.handler_name in EXCLUDE_AUTH_HANDLERS:
                _auth_exclude_paths.update(router.paths)

        app_config.openapi_config = OpenAPIConfig(
            title="Security API",  # TODO: make configurable
            version="0.1.0",  # TODO: make configurable
        )
        if self._config.auth_strategy == "session":
            strategy = SessionAuth(
                exclude=[*_auth_exclude_paths],
                retrieve_user_handler=get_retrieve_user_handler(self._config.user_model),
                session_backend_config=self._config.session_backend_config,  # type: ignore
            )
            app_config = strategy.on_app_init(app_config)

        app_config.route_handlers.extend(route_handlers)

        return app_config

    def _get_route_handlers(self) -> List[Union[HTTPRouteHandler, Router]]:
        """Parse the route handler configs to get Routers."""

        handlers = []
        if self._config.auth_handler_config:
            handlers.append(
                get_auth_handler(
                    login_path=self._config.auth_handler_config.login_path,
                    logout_path=self._config.auth_handler_config.logout_path,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=get_service_dependency(self._config.user_model, self._config.user_service_class),
                )
            )
        if self._config.current_user_handler_config:
            handlers.append(
                get_current_user_handler(
                    path=self._config.current_user_handler_config.path,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=get_service_dependency(self._config.user_model, self._config.user_service_class),
                )
            )
        if self._config.password_reset_handler_config:
            handlers.append(
                get_password_reset_handler(
                    forgot_path=self._config.password_reset_handler_config.forgot_path,
                    reset_path=self._config.password_reset_handler_config.reset_path,
                    service_dependency=get_service_dependency(self._config.user_model, self._config.user_service_class),
                )
            )
        if self._config.register_handler_config:
            handlers.append(
                get_registration_handler(
                    path=self._config.register_handler_config.path,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=get_service_dependency(self._config.user_model, self._config.user_service_class),
                )
            )
        if self._config.user_management_handler_config:
            handlers.append(
                get_user_management_handler(
                    path_prefix=self._config.user_management_handler_config.path_prefix,
                    authorized_roles=self._config.user_management_handler_config.authorized_roles,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=get_service_dependency(self._config.user_model, self._config.user_service_class),
                )
            )
        if self._config.verification_handler_config:
            handlers.append(
                get_verification_handler(
                    path=self._config.verification_handler_config.path,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=get_service_dependency(self._config.user_model, self._config.user_service_class),
                )
            )
        return handlers
