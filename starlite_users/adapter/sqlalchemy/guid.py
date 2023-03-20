"""Modified from https://docs.sqlalchemy.org/en/14/core/custom_types.html#backend-agnostic-guid-type Copyright 2005-2022
SQLAlchemy authors and contributors.
"""
from typing import Any, Union
from uuid import UUID

from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import CHAR, TypeDecorator

__all__ = ["GUID"]


class GUID(TypeDecorator):  # pylint: disable=W0223
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(32), storing as stringified hex values.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        """Return a `.TypeEngine` object corresponding to a dialect."""

        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))

        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value: Any, dialect: Any) -> Union[Any, str]:
        """Receive a bound parameter value to be converted."""

        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)

        if not isinstance(value, UUID):
            return str(UUID(value))

        return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> Union[Any, UUID]:
        """Receive a result-row column value to be converted."""

        if value is None:
            return value

        if not isinstance(value, UUID):
            return UUID(value)

        return value
