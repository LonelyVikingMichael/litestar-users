from typing import TypeVar
from uuid import uuid4

from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base, Mapped
from sqlalchemy.dialects.postgresql import UUID


class _Base:
    """Base for SQLAlchemy models."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, nullable=False)  # TODO: dynamic type


Base = declarative_base(cls=_Base)


class User(Base):
    __tablename__ = 'user'

    email: Mapped[str] = Column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = Column(String(1024))


DatabaseModelType = TypeVar('DatabaseModelType', bound=Base)
