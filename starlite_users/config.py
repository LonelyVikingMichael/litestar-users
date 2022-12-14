from typing import Any, List, Generic, Literal, Optional, Tuple, Type, Union

from pydantic import BaseModel, SecretStr, root_validator
from starlite import HTTPRouteHandler, Router, State
from starlite.middleware.session.base import BaseBackendConfig

from .models import UserModelType
from .schema import UserCreateDTOType, UserReadDTOType, UserUpdateDTOType


class AuthHandlerConfig(BaseModel):
    login_path: str = '/login'
    logout_path: str = '/logout'


class RegisterHandlerConfig(BaseModel):
    path: str = '/register'


class CurrentUserHandlerConfig(BaseModel):
    path: str = '/users/me'


class UserManagementHandlerConfig(BaseModel):
    path_prefix: str = '/users'
    authorized_roles: Tuple[str] = ('administrator',)


class VerificationHandlerConfig(BaseModel):
    path: str = '/verify'


class PasswordResetHandlerConfig(BaseModel):
    forgot_path: str = '/forgot-password'
    reset_path: str = '/reset-password'


class RouteHandlerConfig(BaseModel):
    """The configurations provided are used to configure and register
    Starlite-Users route handlers.
    """

    auth_handler_config: Optional[AuthHandlerConfig]
    current_user_handler_config: Optional[CurrentUserHandlerConfig]
    password_reset_handler_config: Optional[PasswordResetHandlerConfig]
    register_handler_config: Optional[RegisterHandlerConfig]
    user_management_handler_config: Optional[UserManagementHandlerConfig]
    verification_handler_config: Optional[VerificationHandlerConfig]

    @root_validator
    def validate_config(cls, values: Any):
        if all(value is None for value in values.values()):
            raise ValueError('at least one route handler must be registered')
        return values


class StarliteUsersConfig(BaseModel, Generic[UserModelType]):
    """Configuration class for StarliteUsersPlugin."""

    class Config:
        arbitrary_types_allowed = True

    auth_exclude_paths: List[str] = []
    auth_strategy: Literal['session', 'jwt']
    route_handler_config: RouteHandlerConfig
    secret: SecretStr
    session_backend_config: Optional[BaseBackendConfig] = None
    user_model: Type[UserModelType]
    user_read_dto: Type[UserReadDTOType]

    @root_validator
    def validate_auth_backend(cls, values: Any):
        if values.get('auth_strategy') == 'session' and not values.get('session_backend_config'):
            raise ValueError('session_backend_config must be set when auth_strategy is set to "session"')
        return values

    def _set_state(self, state: State):
        state.starlite_users_config = {
            'user_model': self.user_model,
            'secret': self.secret,
        }