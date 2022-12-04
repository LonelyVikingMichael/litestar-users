class UserException(Exception):
    """Base user exception."""


class UserNotFoundException(UserException):
    """Raise when a user is expected but none is found."""


class UserConflictException(UserException):
    """Raise when db constraints are violated."""
