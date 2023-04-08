# Role based route guards

Starlite-Users provides the following guard provider functions that you may use on your own route handlers:

* `roles_accepted`: The user must have _at least one_ of the listed roles in order to access the resource.
* `roles_required`: The user must have _all_ the listed roles in order to access the resource.

Example:

```python
from typing import Any

from litestar import get
from starlite_users.guards import roles_accepted, roles_required


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
    Usually, guard params in Starlite should not be invoked. We do invoke the `roles_accepted` and `roles_required` functions though, as they return functions which meet the requirements.
