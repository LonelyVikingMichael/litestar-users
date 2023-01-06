from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from starlite.contrib.jwt import Token

from .constants import ENCODING_SECRET

if TYPE_CHECKING:
    from uuid import UUID

    from starlite.testing import TestClient

    from starlite_users import StarliteUsersConfig


def create_jwt(identifier: str) -> str:
    token = Token(exp=datetime.now() + timedelta(days=1), sub=identifier)
    return token.encode(secret=ENCODING_SECRET.get_secret_value(), algorithm="HS256")


class MockAuth:
    """Mock class to be used in authentication fixtures."""

    def __init__(self, client: "TestClient", config: "StarliteUsersConfig") -> None:
        self.client = client
        self.config = config

    def authenticate(self, user_id: "UUID") -> None:
        """Authenticate a TestClient request.

        Works with both session and JWT backends.
        """

        if self.config.auth_backend == "session":
            self.client.set_session_data({"user_id": str(user_id)})
        elif self.config.auth_backend == "jwt" or self.config.auth_backend == "jwt_cookie":
            token = create_jwt(str(user_id))
            self.client.headers["Authorization"] = "Bearer " + token
