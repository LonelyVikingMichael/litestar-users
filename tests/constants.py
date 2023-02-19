from pydantic import SecretStr

ENCODING_SECRET = SecretStr("1234567890abcdef")
DEFAULT_AUTH_EXCLUDE_PATHS = ("/login", "/register", "/verify", "/forgot-password", "/reset-password")
