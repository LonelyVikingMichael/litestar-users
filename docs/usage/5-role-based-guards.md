# Role based route guards

Litestar-Users provides the following guard provider functions:

* `roles_accepted`: The user must have _at least one_ of the listed roles in order to access the resource.
* `roles_required`: The user must have _all_ the listed roles in order to access the resource.

Example:

```python
from typing import Any

from litestar import get
from litestar_users.guards import roles_accepted, roles_required


@get("/sensitive-info", guards=[roles_accepted("admin", "accountant")])
def sensitive_info() -> Any:
    """Accessible only by users with admin or accountant roles."""
    ...


@get("/super-sensitive-info", guards=[roles_required("admin", "accountant")])
def extra_sensitive_info() -> Any:
    """Accessible only by users with both admin and accountant roles."""
    ...
```

!!! important
    Usually, guard params in Litestar should not be invoked since they are called internally. We **do** invoke the `roles_accepted` and `roles_required` functions though, as they return callables which meet the requirements.
