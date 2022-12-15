from typing import Tuple, Union

from passlib.context import CryptContext
from pydantic import SecretStr


class PasswordManager:
    """Thin wrapper around `passlib`."""

    def __init__(self):
        self.context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_hash(self, password: SecretStr) -> str:
        """Create a password hash.

        Args:
            password: The password to hash.
        """
        return self.context.hash(password.get_secret_value())

    def verify_and_update(self, password: SecretStr, password_hash: str) -> Tuple[bool, Union[str, None]]:
        """Verify and re-hash a password.

        Args:
            password: The password to verify.
            password_hash: The hash to verify against.
        """
        return self.context.verify_and_update(password.get_secret_value(), password_hash)
