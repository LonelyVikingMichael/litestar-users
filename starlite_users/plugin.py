from typing import Any, TYPE_CHECKING

from starlite.plugins.base import PluginProtocol
from starlite import Router, HTTPRouteHandler, OpenAPIConfig
from starlite.security.session_auth import SessionAuth

from .config import StarliteUsersConfig
from .service import get_retrieve_user_handler

if TYPE_CHECKING:
    from starlite.config import AppConfig

EXCLUDE_AUTH_HANDLERS = ('login', 'register', 'verify', 'forgot_password', 'reset_password')


class StarliteUsersPlugin(PluginProtocol[Any]):
    """A Plugin for authentication and user management."""

    def __init__(
        self,
        config: StarliteUsersConfig
    ) -> None:
        self._config = config

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        _auth_exclude_paths = set(*self._config.auth_exclude_paths)
        for router in self._config.route_handlers:
            if isinstance(router, Router):
                for route in router.routes:
                    if any(name in EXCLUDE_AUTH_HANDLERS for name in route.handler_names):
                        _auth_exclude_paths.add(route.path)
            if isinstance(router, HTTPRouteHandler) and router.handler_name in EXCLUDE_AUTH_HANDLERS:
                _auth_exclude_paths.update(router.paths)

        app_config.openapi_config = OpenAPIConfig(
            title='Security API',  # TODO: make configurable
            version='0.1.0',  # TODO: make configurable
        )
        if self._config.auth_strategy == 'session':
            strategy = SessionAuth(
                exclude=[*_auth_exclude_paths],
                retrieve_user_handler=get_retrieve_user_handler(self._config.user_model),
                session_backend_config=self._config.session_backend_config,  # type: ignore
            )
            app_config = strategy.on_app_init(app_config)

        app_config.route_handlers.extend(self._config.route_handlers)
        app_config.on_startup.append(self._config._set_state)

        return app_config
