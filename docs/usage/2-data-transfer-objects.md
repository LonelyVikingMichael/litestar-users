# Data transfer objects (DTOs)

Litestar-Users provides base `pydantic` models to be subclassed and registered on `LitestarUsersConfig`. This is necessary to properly type the built-in route handlers, and by extension the OpenAPI documentation.

## User DTOs

You must set up the following 3 `User` models:

```python
from litestar_users.schema import BaseUserCreateDTO, BaseUserReadDTO, BaseUserUpdateDTO


class UserCreateDTO(UserCreateDTO):
    pass


class UserReadDTO(UserReadDTO):
    pass


class UserUpdateDTO(UserUpdateDTO):
    pass
```

Or, if you added custom fields to your database models, for example `token_count` column:

```python
from typing import Optional

from litestar_users.schema import BaseUserCreateDTO, BaseUserReadDTO, BaseUserUpdateDTO


class UserCreateDTO(UserCreateDTO):
    token_count: int


class UserReadDTO(UserReadDTO):
    token_count: int


class UserUpdateDTO(UserUpdateDTO):
    token_count: Optional[int]
```

## Role DTOs

These are only required if you wish to register administrative role management route handlers.

```python
from litestar_users.schema import BaseRoleCreateDTO, BaseRoleReadDTO, BaseRoleUpdateDTO


class RoleCreateDTO(RoleCreateDTO):
    pass


class RoleReadDTO(RoleReadDTO):
    pass


class RoleUpdateDTO(RoleUpdateDTO):
    pass
```

Or, if you added custom fields to your database models, for example a `permissions` column:

```python
from typing import Optional

from litestar_users.schema import BaseRoleCreateDTO, BaseRoleReadDTO, BaseRoleUpdateDTO


class RoleCreateDTO(RoleCreateDTO):
    permissions: str


class RoleReadDTO(RoleReadDTO):
    permissions: str


class RoleUpdateDTO(RoleUpdateDTO):
    permissions: Optional[str]
```
