from typing import TYPE_CHECKING, Type

from starlite.exceptions import (
    HTTPException,
    InternalServerException,
)
from starlite.middleware.exceptions.debug_response import create_debug_response
from starlite.utils.exception import create_exception_response

__all__ = [
    "ConflictException",
    "ExpiredTokenException",
    "InvalidException",
    "InvalidTokenException",
    "RepositoryConflictException",
    "RepositoryException",
    "RepositoryNotFoundException",
    "TokenException",
    "repository_exception_handler",
    "token_exception_handler",
]


if TYPE_CHECKING:
    from starlite import Request, Response


class TokenException(Exception):
    """Base token exception."""


class InvalidTokenException(TokenException):
    """Raise when a JWT is found to be invalid."""


class ExpiredTokenException(TokenException):
    """Raise when a JWT is found to be expired."""


class ConflictException(HTTPException):
    """Generic HTTP conflict exception."""

    status_code = 409


class InvalidException(HTTPException):
    """Generic HTTP invalid exception."""

    status_code = 400


def _create_exception_response(
    request: "Request", exception: Exception, http_exception: Type[HTTPException]
) -> "Response":
    """Create an appropriate response depending on `request.app.debug` value."""
    if http_exception is InternalServerException and request.app.debug:
        return create_debug_response(request, exception)
    return create_exception_response(http_exception())


def token_exception_handler(request: "Request", exception: TokenException) -> "Response":
    """Transform token exceptions to HTTP exceptions."""

    http_exception: type[HTTPException]
    if isinstance(exception, (InvalidTokenException, ExpiredTokenException)):
        http_exception = InvalidException
    else:
        http_exception = InternalServerException
    return _create_exception_response(request, exception, http_exception)
