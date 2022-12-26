from typing import TYPE_CHECKING

from starlite_users.main import EXCLUDE_AUTH_HANDLERS

if TYPE_CHECKING:
    from starlite import Starlite


def test_auth_exclude_paths(app: "Starlite") -> None:
    if app.middleware[0].kwargs.get("config"):
        excluded_paths = app.middleware[0].kwargs["config"].exclude
    elif app.middleware[0].kwargs.get("exclude"):
        excluded_paths = app.middleware[0].kwargs["exclude"]

    assert all(f'/{handler.replace("_", "-")}' in excluded_paths for handler in EXCLUDE_AUTH_HANDLERS)
