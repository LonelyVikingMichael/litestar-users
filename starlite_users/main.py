from typing import TYPE_CHECKING, List, Union

from starlite import HTTPRouteHandler, OpenAPIConfig, Router
from starlite.contrib.jwt import JWTAuth, JWTCookieAuth
from starlite.security.session_auth import SessionAuth

from starlite_users.config import StarliteUsersConfig
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
from starlite_users.user_handlers import (
    get_jwt_retrieve_user_handler,
    get_session_retrieve_user_handler,
)

if TYPE_CHECKING:
    from starlite.config import AppConfig

EXCLUDE_AUTH_HANDLERS = (
    "login",
    "register",
    "verify",
    "forgot_password",
    "reset_password",
)


class StarliteUsers:
    """A Starlite extension for authentication, authorization and user management."""

    def __init__(self, config: StarliteUsersConfig) -> None:
        self._config = config

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Register routers, auth strategies etc on the Starlite app.

        Args:
            app_config: An instance of [AppConfig][starlite.config.AppConfig]
        """
        auth_exclude_paths = {*self._config.auth_exclude_paths}
        auth_backend = self._get_auth_backend()
        route_handlers = self._get_route_handlers(auth_backend)

        for router in route_handlers:
            if isinstance(router, Router):
                for route in router.routes:
                    if any(name in EXCLUDE_AUTH_HANDLERS for name in route.handler_names):
                        auth_exclude_paths.add(route.path)
            if isinstance(router, HTTPRouteHandler) and router.handler_name in EXCLUDE_AUTH_HANDLERS:
                auth_exclude_paths.update(router.paths)

        app_config.openapi_config = OpenAPIConfig(
            title="Security API",  # TODO: make configurable
            version="0.1.0",  # TODO: make configurable
        )
        auth_backend.exclude.extend(auth_exclude_paths)
        app_config = auth_backend.on_app_init(app_config)
        app_config.route_handlers.extend(route_handlers)

        exception_handlers = {
            TokenException: token_exception_handler,
            RepositoryException: repository_exception_handler,
        }
        app_config.exception_handlers.update(exception_handlers)

        return app_config

    def _get_auth_backend(self):
        if self._config.auth_backend == "session":
            auth_backend = SessionAuth[self._config.user_model](
                retrieve_user_handler=get_session_retrieve_user_handler(
                    self._config.user_model, self._config.role_model
                ),
                session_backend_config=self._config.session_backend_config,  # type: ignore
                exclude=[],
            )
        elif self._config.auth_backend == "jwt":
            auth_backend = JWTAuth[self._config.user_model](
                retrieve_user_handler=get_jwt_retrieve_user_handler(self._config.user_model, self._config.role_model),
                token_secret=self._config.secret.get_secret_value(),
                exclude=[],
            )
        elif self._config.auth_backend == "jwt_cookie":
            auth_backend = JWTCookieAuth(
                retrieve_user_handler=get_jwt_retrieve_user_handler(self._config.user_model, self._config.role_model),
                token_secret=self._config.secret.get_secret_value(),
                exclude=[],
            )
        return auth_backend

    def _get_route_handlers(
        self, auth_backend: Union[JWTAuth, JWTCookieAuth, SessionAuth]
    ) -> List[Union[HTTPRouteHandler, Router]]:
        """Parse the route handler configs to get Routers."""

        handlers = []
        if self._config.auth_handler_config:
            handlers.append(
                get_auth_handler(
                    login_path=self._config.auth_handler_config.login_path,
                    logout_path=self._config.auth_handler_config.logout_path,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=get_service_dependency(
                        self._config.user_model, self._config.role_model, self._config.user_service_class
                    ),
                    auth_backend=auth_backend,
                )
            )
        if self._config.current_user_handler_config:
            handlers.append(
                get_current_user_handler(
                    path=self._config.current_user_handler_config.path,
                    user_read_dto=self._config.user_read_dto,
                    user_update_dto=self._config.user_update_dto,
                    service_dependency=get_service_dependency(
                        self._config.user_model, self._config.role_model, self._config.user_service_class
                    ),
                )
            )
        if self._config.password_reset_handler_config:
            handlers.append(
                get_password_reset_handler(
                    forgot_path=self._config.password_reset_handler_config.forgot_path,
                    reset_path=self._config.password_reset_handler_config.reset_path,
                    service_dependency=get_service_dependency(
                        self._config.user_model, self._config.role_model, self._config.user_service_class
                    ),
                )
            )
        if self._config.register_handler_config:
            handlers.append(
                get_registration_handler(
                    path=self._config.register_handler_config.path,
                    user_create_dto=self._config.user_create_dto,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=get_service_dependency(
                        self._config.user_model, self._config.role_model, self._config.user_service_class
                    ),
                )
            )
        if self._config.role_management_handler_config:
            handlers.append(
                get_role_management_handler(
                    path_prefix=self._config.role_management_handler_config.path_prefix,
                    assign_role_path=self._config.role_management_handler_config.assign_role_path,
                    revoke_role_path=self._config.role_management_handler_config.revoke_role_path,
                    authorized_roles=self._config.role_management_handler_config.authorized_roles,
                    role_create_dto=self._config.role_create_dto,
                    role_read_dto=self._config.role_read_dto,
                    role_update_dto=self._config.role_update_dto,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=get_service_dependency(
                        self._config.user_model, self._config.role_model, self._config.user_service_class
                    ),
                )
            )
        if self._config.user_management_handler_config:
            handlers.append(
                get_user_management_handler(
                    path_prefix=self._config.user_management_handler_config.path_prefix,
                    authorized_roles=self._config.user_management_handler_config.authorized_roles,
                    user_read_dto=self._config.user_read_dto,
                    user_update_dto=self._config.user_update_dto,
                    service_dependency=get_service_dependency(
                        self._config.user_model, self._config.role_model, self._config.user_service_class
                    ),
                )
            )
        if self._config.verification_handler_config:
            handlers.append(
                get_verification_handler(
                    path=self._config.verification_handler_config.path,
                    user_read_dto=self._config.user_read_dto,
                    service_dependency=get_service_dependency(
                        self._config.user_model, self._config.role_model, self._config.user_service_class
                    ),
                )
            )
        return handlers
