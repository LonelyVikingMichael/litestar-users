from pydantic import BaseModel
from starlite.plugins.base import PluginProtocol


class StarliteUsersPlugin(PluginProtocol):
    """A Plugin for authentication and user management."""

    def __init__(self) -> None:
        pass
