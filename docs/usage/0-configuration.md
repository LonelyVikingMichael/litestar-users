# Configuration

A few dependencies need to be configured before you can get started.

## User and Role models

Model configuration is documented [here](./1-database-models.md).

## DTOs

DTO configuration is documented [here](./2-data-transfer-objects.md).

## The user service

User service setup is documented [here](./3-the-user-service.md).

## Setting up `LitestarUsersConfig`

Once the above is in place, all that's left is registering the desired [route handlers](./4-route-handler-configs.md) and registering an instance of `LitestarUsers` on your Litestar application, as shown below:

```python
from litestar import Litestar
from litestar_users import LitestarUsers, LitestarUsersConfig
from litestar_users.config import AuthHandlerConfig

from my.models import User
from my.schemas import UserReadDTO

config = LitestarUsersConfig(
    user_model=User, user_read_dto=UserReadDTO, auth_handler_config=AuthHandlerConfig()
)
litestar_users = LitestarUsers(config=config)

app = Litestar(
    on_app_init=[litestar_users.on_app_init],
    route_handlers=[],
)
```

!!! note
    Aside from the pre-configured public routes provided by Litestar-Users, *all* the routes on your application will require authentication unless specified otherwise in [LitestarUsersConfig.auth_exclude_paths][litestar_users.config.LitestarUsersConfig.auth_exclude_paths]

!!! note
    Litestar-Users requires the use of a corresponding `Litestar` [plugin](https://litestarproject.dev/lib/usage/plugins/index.html) for database management.
