from typing import TYPE_CHECKING

from starlite_users.plugin import EXCLUDE_AUTH_HANDLERS

if TYPE_CHECKING:
    from starlite import Starlite


def test_auth_exclude_paths(app: 'Starlite') -> None:
    assert (
        sorted(app.middleware[0].kwargs['config'].exclude)
        == [f'/{handler.replace("_", "-")}' for handler in sorted(EXCLUDE_AUTH_HANDLERS)]
    )
