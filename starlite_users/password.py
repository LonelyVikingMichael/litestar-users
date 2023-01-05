from typing import TYPE_CHECKING, Optional, Tuple, cast

from passlib.context import CryptContext

if TYPE_CHECKING:
    from pydantic import SecretStr


class PasswordManager:
    """Thin wrapper around `passlib`."""

    def __init__(self) -> None:
        """Construct a PasswordManager."""

        self.context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_hash(self, password: "SecretStr") -> str:
        """Create a password hash.

        Args:
            password: The password to hash.
        """
        return cast("str", self.context.hash(password.get_secret_value()))

    def verify_and_update(self, password: "SecretStr", password_hash: str) -> Tuple[bool, Optional[str]]:
        """Verify a password and rehash it if the hash is deprecated.

        Args:
            password: The password to verify.
            password_hash: The hash to verify against.
        """
        return cast(
            "Tuple[bool, Optional[str]]", self.context.verify_and_update(password.get_secret_value(), password_hash)
        )
