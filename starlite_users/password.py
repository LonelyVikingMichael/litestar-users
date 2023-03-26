from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence, Tuple, cast

from passlib.context import CryptContext

__all__ = ["PasswordManager"]


if TYPE_CHECKING:
    from pydantic import SecretStr


class PasswordManager:
    """Thin wrapper around `passlib`."""

    def __init__(self, hash_schemes: Sequence[str] | None = None) -> None:
        """Construct a PasswordManager.

        Args:
            hash_schemes: The encryption schemes to use. Defaults to ["argon2"].
        """
        if hash_schemes is None:
            hash_schemes = ["argon2"]
        self.context = CryptContext(schemes=hash_schemes, deprecated="auto")

    def hash(self, password: "SecretStr") -> str:
        """Create a password hash.

        Args:
            password: The password to hash.
        """
        return cast("str", self.context.hash(password.get_secret_value()))

    def verify_and_update(self, password: "SecretStr", password_hash: str) -> tuple[bool, str | None]:
        """Verify a password and rehash it if the hash is deprecated.

        Args:
            password: The password to verify.
            password_hash: The hash to verify against.
        """
        return cast(
            "Tuple[bool, Optional[str]]", self.context.verify_and_update(password.get_secret_value(), password_hash)
        )
