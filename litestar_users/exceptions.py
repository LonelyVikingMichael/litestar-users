from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_alchemy.exceptions import ConflictError, NotFoundError, RepositoryError
from litestar.exceptions import (
    HTTPException,
    InternalServerException,
    NotFoundException,
)
from litestar.middleware.exceptions._debug_response import create_debug_response
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


def token_exception_handler(request: Request, exception: TokenException) -> Response:
    """Transform token exceptions to HTTP exceptions."""
    http_exception: type[HTTPException]
    if isinstance(exception, (InvalidTokenException, ExpiredTokenException)):
        http_exception = InvalidException
    else:
        http_exception = InternalServerException
    if request.app.debug:
        return create_debug_response(request, exception)
    return create_exception_response(request=request, exc=http_exception(detail=str(exception)))


def repository_exception_to_http_response(request: Request, exception: RepositoryError) -> Response:
    """Transform repository exceptions to HTTP exceptions.

    Args:
        request: The request that experienced the exception.
        exception: Exception raised during handling of the request.

    Returns:
        Exception response appropriate to the type of original exception.
    """
    http_exception: type[HTTPException]
    if isinstance(exception, NotFoundError):
        http_exception = NotFoundException
    elif isinstance(exception, ConflictError):
        http_exception = ConflictException
    else:
        http_exception = InternalServerException
    if request.app.debug and not request.app.state.get("testing"):
        return create_debug_response(request, exception)
    return create_exception_response(request=request, exc=http_exception(detail=str(exception)))
