from typing import TYPE_CHECKING, Any, Callable, Dict, List, Sequence, Type, Union

from starlite import HTTPRouteHandler, OpenAPIConfig, Request, Response, Router
from starlite.contrib.jwt import JWTAuth, JWTCookieAuth
from starlite.security.session_auth import SessionAuth

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

    from starlite_users.config import StarliteUsersConfig

EXCLUDE_AUTH_HANDLERS = (
    "login",
    "register",
    "verify",
    "forgot_password",
    "reset_password",
)


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
        # will always be true
        if isinstance(auth_backend.exclude, list):
            auth_backend.exclude.extend(auth_exclude_paths)
        app_config = auth_backend.on_app_init(app_config)
        app_config.route_handlers.extend(route_handlers)

        exception_handlers: Dict[Type[Exception], Callable[[Request, Any], Response]] = {
            TokenException: token_exception_handler,
            RepositoryException: repository_exception_handler,
        }
        app_config.exception_handlers.update(exception_handlers)  # type: ignore[arg-type]

        return app_config

    def _get_auth_backend(self) -> Union[JWTAuth, JWTCookieAuth, SessionAuth]:
        if self._config.auth_backend == "session":
            return SessionAuth(
                retrieve_user_handler=get_session_retrieve_user_handler(
                    self._config.user_model, self._config.role_model
                ),
                session_backend_config=self._config.session_backend_config,  # type: ignore
                exclude=[],
            )
        if self._config.auth_backend == "jwt":
            return JWTAuth(
                retrieve_user_handler=get_jwt_retrieve_user_handler(self._config.user_model, self._config.role_model),
                token_secret=self._config.secret.get_secret_value(),
                exclude=[],
            )

        return JWTCookieAuth(
            retrieve_user_handler=get_jwt_retrieve_user_handler(self._config.user_model, self._config.role_model),
            token_secret=self._config.secret.get_secret_value(),
            exclude=[],
        )

    def _get_route_handlers(
        self, auth_backend: Union[JWTAuth, JWTCookieAuth, SessionAuth]
    ) -> Sequence[Union[HTTPRouteHandler, Router]]:
        """Parse the route handler configs to get Routers."""

        handlers: List[Union[HTTPRouteHandler, Router]] = []
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
                    guards=self._config.role_management_handler_config.guards,
                    opt=self._config.role_management_handler_config.opt,
                    role_create_dto=self._config.role_create_dto,  # type: ignore[arg-type]
                    role_read_dto=self._config.role_read_dto,  # type: ignore[arg-type]
                    role_update_dto=self._config.role_update_dto,  # type: ignore[arg-type]
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
                    guards=self._config.user_management_handler_config.guards,
                    opt=self._config.user_management_handler_config.opt,
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
