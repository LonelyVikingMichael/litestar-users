from typing import Any, Union, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, EmailStr
from starlite.plugins.base import PluginProtocol
from starlite.security.session_auth import SessionAuth
from starlite.contrib.jwt import JWTAuth
from starlite import Router
from starlite.middleware.session.base import BaseBackendConfig

from .route_handlers import user_router

if TYPE_CHECKING:
    from starlite import Starlite

class StarliteUsersConfig(BaseModel):
    """Configuration for StarliteUsersPlugin."""

    class Config:
        arbitrary_types_allowed = True

    auth_strategy: Union[SessionAuth, JWTAuth]
    router: Router = user_router
    session_backend_config: BaseBackendConfig = None


class StarliteUsersPlugin(PluginProtocol[Any]):
    """A Plugin for authentication and user management."""

    def __init__(
        self,
        config: StarliteUsersConfig = None
    ) -> None:
        self._config = config

    def on_app_init(self, app: "Starlite") -> None:
        if isinstance(self._config.auth_strategy, SessionAuth):
            self._config.auth_strategy.session_backend_config = self._config.session_backend_config
        self._config.auth_strategy.on_app_init()
        app.register(self._config.router)
