# Database models

## The user model

You must define and register an ORM `User` model for use with the data persistence layer. Generic mixins are provided to be subclassed and extended if needed. The user mixin provides the following default columns:

* `id`: UUID
* `email`: str
* `password_hash`: str
* `is_active`: bool
* `is_verified`: bool

### SQLAlchemy User

!!! important
    If you're using SQLAlchemy models, Starlite-Users is reliant on the [SQLAlchemyPlugin][starlite.plugins.sql_alchemy.SQLAlchemyPlugin] for session management and dependency injection. This ensures that only a single session is created and used per request. Please see the Starlite documentation for setup directions.

```python
from starlite_users.adapter.sqlalchemy.mixins import SQLAlchemyUserMixin
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base, SQLAlchemyUserMixin):
    __tablename__ = "user"
```

You can also declare arbitrary custom columns:

```python
from starlite_users.adapter.sqlalchemy.mixins import SQLAlchemyUserMixin
from sqlalchemy import Column, Integer

from my.models.base import Base  # declarative_base class


class User(Base, SQLAlchemyUserMixin):
    __tablename__ = "user"

    token_count = Column(Integer())
```

## The role model

Required only if you wish to register administrative role management route handlers. You must also register a users-to-roles association table, since `user.roles` is a many-to-many relationship type.

!!! note
    You must set your own `User.roles` relationship and association table, since this is dependent on your own `__tablename__` definitions.

### SQLAlchemy Role

```python
from sqlalchemy.orm import relationship
from starlite_users.adapter.sqlalchemy.mixins import (
    SQLAlchemyUserMixin,
    SQLAlchemyRoleMixin,
)

from my.models.base import Base  # declarative_base class


class User(Base, SQLAlchemyUserMixin):
    __tablename__ = "user"

    roles = relationship("Role", secondary="user_role", lazy="joined")


class Role(Base, SQLAlchemyRoleMixin):
    __tablename__ = "role"


class UserRole(Base):
    __tablename__ = "user_role"
```

Just as with the user model, you can define arbitrary custom columns:

```python
from datetime import datetime

from starlite_users.adapter.sqlalchemy.mixins import SQLAlchemyRoleMixin
from sqlalchemy import Column, DateTime

from my.models.base import Base  # declarative_base class


class Role(Base, SQLAlchemyRoleMixin):
    created_at = Column(DateTime(), default=datetime.now)
```
