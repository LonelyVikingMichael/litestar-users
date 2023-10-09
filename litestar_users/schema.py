from dataclasses import dataclass
from uuid import UUID

__all__ = [
    "ForgotPasswordSchema",
    "ResetPasswordSchema",
    "AuthenticationSchema",
    "UserRoleSchema",
]


@dataclass
class AuthenticationSchema:
    """User authentication schema."""

    email: str
    password: str


@dataclass
class ForgotPasswordSchema:
    """Forgot password schema."""

    email: str


@dataclass
class ResetPasswordSchema:
    """Reset password schema."""

    token: str
    password: str


@dataclass
class UserRoleSchema:
    """User role association schema."""

    user_id: UUID
    role_id: UUID
