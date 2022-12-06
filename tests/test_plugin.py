from starlite.testing import TestClient
import pytest

from starlite_users.plugin import StarliteUsersPlugin, StarliteUsersConfig


@pytest.fixture
def test_plugin():
    starlite_users = StarliteUsersPlugin(
        config=StarliteUsersConfig(
            
        )
    )