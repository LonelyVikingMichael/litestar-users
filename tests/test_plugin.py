from typing import TYPE_CHECKING

from starlite_users.plugin import EXCLUDE_AUTH_HANDLERS

if TYPE_CHECKING:
    from starlite import Starlite


def test_auth_exclude_paths(app: "Starlite") -> None:
    assert all(
        f'/{handler.replace("_", "-")}' in app.middleware[0].kwargs["config"].exclude
        for handler in EXCLUDE_AUTH_HANDLERS
    )
