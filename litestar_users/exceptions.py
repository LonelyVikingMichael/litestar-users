from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.contrib.repository.exceptions import (
    ConflictError as RepositoryConflictException,
)
from litestar.contrib.repository.exceptions import (
    NotFoundError as RepositoryNotFoundException,
)
from litestar.contrib.repository.exceptions import (
    RepositoryError as RepositoryException,
)
from litestar.exceptions import (
    HTTPException,
    InternalServerException,
    NotFoundException,
)
from litestar.middleware.exceptions.middleware import create_exception_response

__all__ = [
    "ExpiredTokenException",
    "InvalidException",
    "InvalidTokenException",
    "TokenException",
    "token_exception_handler",
]


if TYPE_CHECKING:
    from litestar import Request, Response


class TokenException(Exception):
    """Base token exception."""


class InvalidTokenException(TokenException):
    """Raise when a JWT is found to be invalid."""


class ExpiredTokenException(TokenException):
    """Raise when a JWT is found to be expired."""


class InvalidException(HTTPException):
    """Generic HTTP invalid exception."""

    status_code = 400


class ConflictException(HTTPException):
    status_code = 409


def token_exception_handler(_: Request, exception: TokenException) -> Response:
    """Transform token exceptions to HTTP exceptions."""
    http_exception: type[HTTPException]
    if isinstance(exception, (InvalidTokenException, ExpiredTokenException)):
        http_exception = InvalidException
    else:
        http_exception = InternalServerException
    return create_exception_response(http_exception())


def repository_exception_to_http_response(_: "Request", exc: RepositoryException) -> "Response":
    """Transform repository exceptions to HTTP exceptions.

    Args:
        _: The request that experienced the exception.
        exc: Exception raised during handling of the request.

    Returns:
        Exception response appropriate to the type of original exception.
    """
    http_exc: type[HTTPException]
    if isinstance(exc, RepositoryNotFoundException):
        http_exc = NotFoundException
    elif isinstance(exc, RepositoryConflictException):
        http_exc = ConflictException
    else:
        http_exc = InternalServerException
    return create_exception_response(http_exc())
