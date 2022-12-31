# Data transfer objects (DTOs)

Starlite-Users provides base `pydantic` models to be subclassed and registered on `StarliteUsersConfig`. This is necessary to properly type the built-in route handlers, and by extension the OpenAPI documentation.

## User DTOs

You must set up the following 3 `User` models:

```python
from starlite_users.schema import BaseUserCreateDTO, BaseUserReadDTO, BaseUserUpdateDTO


class UserCreateDTO(BaseUserCreateDTO):
    pass


class UserReadDTO(BaseUserReadDTO):
    pass


class UserUpdateDTO(BaseUserUpdateDTO):
    pass
```
Or, if you added custom fields to your database models, for example `token_count` column:
```python
from typing import Optional

from starlite_users.schema import BaseUserCreateDTO, BaseUserReadDTO, BaseUserUpdateDTO


class UserCreateDTO(BaseUserCreateDTO):
    token_count: int


class UserReadDTO(BaseUserReadDTO):
    token_count: int


class UserUpdateDTO(BaseUserUpdateDTO):
    token_count: Optional[int]
```

## Role DTOs

These are only required if you wish to register administrative role management route handlers.

```python
from starlite_users.schema import BaseRoleCreateDTO, BaseRoleReadDTO, BaseRoleUpdateDTO


class RoleCreateDTO(BaseRoleCreateDTO):
    pass


class RoleReadDTO(BaseRoleReadDTO):
    pass


class RoleUpdateDTO(BaseRoleUpdateDTO):
    pass
```
Or, if you added custom fields to your database models, for example a `permissions` column:
```python
from typing import Optional

from starlite_users.schema import BaseRoleCreateDTO, BaseRoleReadDTO, BaseRoleUpdateDTO


class RoleCreateDTO(BaseRoleCreateDTO):
    permissions: str


class RoleReadDTO(BaseRoleReadDTO):
    permissions: str


class RoleUpdateDTO(BaseRoleUpdateDTO):
    permissions: Optional[str]
```
