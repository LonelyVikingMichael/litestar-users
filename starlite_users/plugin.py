from typing import Union
from uuid import UUID

from pydantic import BaseModel, EmailStr
from starlite.plugins.base import PluginProtocol
from starlite.security.session_auth import SessionAuth
from starlite.contrib.jwt import JWTAuth


class StarliteUsersConfig(BaseModel):
    auth_strategy: Union[SessionAuth, JWTAuth]


class StarliteUsersPlugin(PluginProtocol):
    """A Plugin for authentication and user management."""

    def __init__(
        self,
        config: StarliteUsersConfig = None
    ) -> None:
        pass
