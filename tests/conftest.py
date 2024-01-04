from litestar_users.password import PasswordManager
from tests.constants import HASH_SCHEMES

pytest_plugins = ["tests.docker_service_fixtures"]
password_manager = PasswordManager(hash_schemes=HASH_SCHEMES)
