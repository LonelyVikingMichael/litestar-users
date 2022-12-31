from typing import Any, Callable

from starlite import BaseRouteHandler, NotAuthorizedException, Request
from starlite.types import Guard

from .adapter.sqlalchemy.mixins import UserModelType


def roles_accepted(*roles: str) -> Guard:
    """Factory to retrieve an authorization `Guard`, injecting authorized role names.

    Args:
        roles: Iterable of authorized role names.

    Returns:
        Starlite [Guard][starlite.types.callable_types.Guard] callable
    """

    def roles_accepted_guard(request: Request[UserModelType, Any], _: BaseRouteHandler) -> None:
        """Authorize a request if any of the user's roles matches any of the supplied roles."""

        if any(role.name in roles for role in request.user.roles):
            return
        raise NotAuthorizedException()

    return roles_accepted_guard


def roles_required(*roles: str) -> Callable:
    """Factory to retrieve an authorization `Guard`, injecting authorized role names.

    Args:
        roles: Iterable of authorized role names.
    """

    def roles_required_guard(request: Request[UserModelType, Any], _: BaseRouteHandler) -> None:
        """Authorize a request if the user's roles matches all of the supplied roles."""

        if all(role.name in roles for role in request.user.roles):
            return
        raise NotAuthorizedException()

    return roles_required_guard
