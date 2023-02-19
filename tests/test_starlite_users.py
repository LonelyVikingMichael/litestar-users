from typing import TYPE_CHECKING

from tests.constants import DEFAULT_AUTH_EXCLUDE_PATHS

if TYPE_CHECKING:
    from starlite import Starlite


def test_auth_exclude_paths(app: "Starlite") -> None:
    if hasattr(app.middleware[0], "kwargs") and app.middleware[0].kwargs.get("config"):  # pyright: ignore
        excluded_paths = app.middleware[0].kwargs["config"].exclude  # pyright: ignore
    elif hasattr(app.middleware[0], "kwargs") and app.middleware[0].kwargs.get("exclude"):  # pyright: ignore
        excluded_paths = app.middleware[0].kwargs["exclude"]  # pyright: ignore

    assert all(path in excluded_paths for path in DEFAULT_AUTH_EXCLUDE_PATHS)  # pyright: ignore
