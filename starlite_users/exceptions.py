class UserException(Exception):
    """Base user exception."""


class UserNotFoundException(UserException):
    """Raise when a user is expected but none is found."""


class UserConflictException(UserException):
    """Raise when db constraints are violated."""


class TokenException(Exception):
    """Base token exception."""


class InvalidTokenException(TokenException):
    """Raise when a JWT is found to be invalid."""


class ExpiredTokenException(TokenException):
    """Raise when a JWT is found to be expired."""
