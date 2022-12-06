from typing import Any, Union, Optional, List, TYPE_CHECKING, Type, Generic

from pydantic import BaseModel
from starlite.plugins.base import PluginProtocol
from starlite.security.session_auth import SessionAuth
from starlite.contrib.jwt import JWTAuth
from starlite import Router, HTTPRouteHandler, Provide
from starlite.middleware.session.base import BaseBackendConfig

from .models import UserModelType

if TYPE_CHECKING:
    from starlite.config import AppConfig


class StarliteUsersConfig(BaseModel, Generic[UserModelType]):
    """Configuration for StarliteUsersPlugin."""

    class Config:
        arbitrary_types_allowed = True

    auth_strategy: Union[SessionAuth, JWTAuth]
    session_backend_config: Optional[BaseBackendConfig] = None
    route_handlers: List[Union[HTTPRouteHandler, Router]]
    user_model: Type[UserModelType]

    def _get_user_model(self) -> Type[UserModelType]:
        return self.user_model


class StarliteUsersPlugin(PluginProtocol[Any]):
    """A Plugin for authentication and user management."""

    def __init__(
        self,
        config: StarliteUsersConfig
    ) -> None:
        self._config = config

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        # if isinstance(self._config.auth_strategy, SessionAuth):
        #     self._config.auth_strategy.session_backend_config = self._config.session_backend_config

        app_config.route_handlers.extend(self._config.route_handlers)
        app_config = self._config.auth_strategy.on_app_init(app_config)
        app_config.dependencies.update({'user_model': Provide(lambda: self._config.user_model)})

        return app_config
