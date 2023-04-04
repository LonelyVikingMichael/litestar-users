from __future__ import annotations

from typing import TYPE_CHECKING

from starlite.exceptions import (
    HTTPException,
    InternalServerException,
)
from starlite.middleware.exceptions.middleware import create_exception_response

__all__ = [
    "ExpiredTokenException",
    "InvalidException",
    "InvalidTokenException",
    "TokenException",
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


class InvalidException(HTTPException):
    """Generic HTTP invalid exception."""

    status_code = 400


def _create_exception_response(request: Request, exception: Exception, http_exception: type[HTTPException]) -> Response:
    """Create an appropriate response depending on `request.app.debug` value."""
    return create_exception_response(http_exception())


def token_exception_handler(request: Request, exception: TokenException) -> Response:
    """Transform token exceptions to HTTP exceptions."""

    http_exception: type[HTTPException]
    if isinstance(exception, (InvalidTokenException, ExpiredTokenException)):
        http_exception = InvalidException
    else:
        http_exception = InternalServerException
    return _create_exception_response(request, exception, http_exception)
