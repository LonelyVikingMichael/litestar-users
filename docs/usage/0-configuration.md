# Configuration

A few dependencies need to be configured before you can get started.

## User and Role models

Model configuration is documented [here](./1-database-models.md).

## DTOs

DTO configuration is documented [here](./2-data-transfer-objects.md).

## The user service

User service setup is documented [here](./3-the-user-service.md).

## Setting up `StarliteUsersConfig`

Once the above is in place, all that's left is registering the desired [route handlers](./4-route-handler-configs.md) and registering an instance of `StarliteUsers` on your Starlite application, as shown below:

```python
from litestar import Starlite
from starlite_users import StarliteUsers, StarliteUsersConfig
from starlite_users.config import AuthHandlerConfig

from my.models import User
from my.schemas import UserReadDTO

config = StarliteUsersConfig(
    user_model=User, user_read_dto=UserReadDTO, auth_handler_config=AuthHandlerConfig()
)
starlite_users = StarliteUsers(config=config)

app = Starlite(
    on_app_init=[starlite_users.on_app_init],
    route_handlers=[],
)
```

!!! note
    Aside from the pre-configured public routes provided by Starlite-Users, *all* the routes on your application will require authentication unless specified otherwise in [StarliteUsersConfig.auth_exclude_paths][starlite_users.config.StarliteUsersConfig.auth_exclude_paths]

!!! note
    Starlite-Users requires the use of a corresponding `Starlite` [plugin](https://starliteproject.dev/lib/usage/plugins/index.html) for database management.
