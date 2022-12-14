from datetime import datetime, timedelta
from typing import Any, Dict, Generic, Optional, Type
from uuid import UUID

from jose import JWTError
from pydantic import SecretStr
from starlite import ASGIConnection, State
from starlite.contrib.jwt.jwt_token import Token
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import UserNotFoundException, InvalidTokenException
from .models import UserModelType
from .password import PasswordManager
from .repository import SQLAlchemyUserRepository
from .schema import UserCreateDTOType, UserUpdateDTOType, UserAuthSchema


class UserService(Generic[UserModelType, UserCreateDTOType, UserUpdateDTOType]):
    """Base class for services integrating to data persistence layers."""

    model_type: Type[UserModelType]

    def __init__(self, repository: SQLAlchemyUserRepository, secret: SecretStr) -> None:
        self.repository = repository
        self.password_manager = PasswordManager()
        self.model_type = repository.model_type
        self.secret = secret

    async def add(self, data: UserCreateDTOType) -> UserModelType:
        """Create a new user programatically."""

        user_dict = data.dict(exclude={'password'})
        user_dict['password_hash'] = self.password_manager.get_hash(data.password)

        user = await self.repository.add(self.model_type(**user_dict))

        return user

    async def register(self, data: UserCreateDTOType) -> UserModelType:
        """Register a new user and optionally run custom business logic."""
        await self.pre_registration_hook(data)

        user = await self.add(data)
        await self.initiate_verification(user)  # TODO: make verification optional?

        await self.post_registration_hook(user)

        return user

    async def get(self, id_: UUID) -> UserModelType:
        """Retrieve a user from the database by id."""

        return await self.repository.get(id_)

    async def get_by(self, **kwargs) -> UserModelType:
        """Retrieve a user from the database by arbitrary keyword arguments."""

        return await self.repository.get_by(**kwargs)

    async def update(self, id_: UUID, data: UserUpdateDTOType) -> UserModelType:
        """Update the given attributes of a user."""

        update_dict = data.dict(exclude={'password'}, exclude_unset=True)
        if data.password:
            update_dict['password_hash'] = self.password_manager.get_hash(data.password)

        return await self.repository.update(id_, update_dict)

    async def delete(self, id_: UUID) -> None:
        """Delete a user with corresponding id."""

        return await self.repository.delete(id_)

    async def authenticate(self, data: UserAuthSchema) -> Optional[UserModelType]:
        """Authenticate a user."""

        if not await self.pre_login_hook(data):
            return

        user = await self.repository.get_by(email=data.email)
        if user is None:
            return

        verified, new_password_hash = self.password_manager.verify_and_update(
            data.password, user.password_hash
        )
        if not verified:
            return
        if new_password_hash is not None:
            user = await self.repository._update(user, {'password_hash': new_password_hash})

        await self.post_login_hook(user)

        return user

    def generate_token(self, user_id: UUID, aud: str) -> str:
        """Generate a timed JWT."""

        token = Token(
            exp=datetime.now() + timedelta(seconds=60 * 60 * 24),  # TODO: make time configurable?
            sub=str(user_id),
            aud=aud
        )
        return token.encode(secret=self.secret.get_secret_value(), algorithm='HS256')

    async def initiate_verification(self, user: UserModelType) -> None:
        """Initiate the user verification flow."""

        token = self.generate_token(user.id, aud='verify')
        await self.send_verifification_token(user, token)

    async def send_verifification_token(self, user: UserModelType, token: str) -> None:
        """Hook to send the verification token to the relevant user."""

        pass

    async def verify(self, encoded_token: str) -> None:
        """Verify a user with the given JWT."""

        token = self._decode_and_verify_token(encoded_token, context='verify')

        user_id = token.sub
        try:
            user = await self.repository.update(user_id, {'is_verified': True})
        except UserNotFoundException as e:
            raise InvalidTokenException from e

        await self.post_verification_hook(user)
        
        return user

    async def initiate_password_reset(self, email: str) -> None:
        user = await self.get_by(email=email)
        token = self.generate_token(user.id, aud='reset_password')
        await self.send_password_reset_token(user, token)

    async def send_password_reset_token(self, user: UserModelType, token: str) -> None:
        """Hook to send the password reset token to the relevant user."""

        pass

    async def reset_password(self, encoded_token: str, password: SecretStr) -> None:
        """Reset a user's password given a valid JWT."""

        token = self._decode_and_verify_token(encoded_token, context='reset_password')

        user_id = token.sub
        try:
            await self.repository.update(user_id, {'password_hash': self.password_manager.get_hash(password)})
        except UserNotFoundException as e:
            raise InvalidTokenException from e

    async def pre_login_hook(self, data: UserAuthSchema) -> bool:
        """Hook to run custom business logic prior to authenticating a user.
        
        Useful for authorization checks agains external sources,
        eg. current membership validity or blacklists, etc
        """

        return True

    async def post_login_hook(self, user: UserModelType) -> None:
        """Hook to run custom business logic after authenticating a user.
        
        Useful for eg. updating a login counter, updating last known user IP
        address, etc.
        """

        pass

    async def pre_registration_hook(self, data: UserCreateDTOType) -> None:
        """Hook to run custom business logic prior to registering a user.
        
        Useful for authorization checks against external sources,
        eg. membership API or blacklists, etc.
        """

        pass

    async def post_registration_hook(self, user: UserModelType) -> None:
        """Hook to run custom business logic after registering a user.
        
        Useful for updating external datasets, sending welcome messages etc.
        It's possible to skip verification entirely by setting `user.is_verified`
        to `True` here.
        """

        pass

    async def post_verification_hook(self, user: UserModelType):
        """Hook to run custom business logic after a user has verified details.
        
        Useful for eg. updating sales lead data, etc.
        """

        pass

    def _decode_and_verify_token(self, encoded_token: str, context: str) -> Token:
        try:
            token = Token.decode(
                encoded_token=encoded_token,
                secret=self.secret.get_secret_value(),
                algorithm='HS256',
            )
        except JWTError as e:
            raise InvalidTokenException from e

        if token.aud != context:
            raise InvalidTokenException(f'aud value must be {context}')
        
        return token


def get_service(session: AsyncSession, state: State):
    """Instantiate service and repository for use with DI."""
    return UserService(
        SQLAlchemyUserRepository(session=session, model_type=state.starlite_users_config['user_model']),
        secret=state.starlite_users_config['secret']
    )


def get_retrieve_user_handler(user_model: Type[UserModelType]):
    async def retrieve_user_handler(session: Dict[str, Any], connection: ASGIConnection) -> Optional[user_model]:
        async_session_maker = connection.app.state.session_maker_class

        async with async_session_maker() as async_session:
            async with async_session.begin():
                repository = SQLAlchemyUserRepository(session=async_session, model_type=user_model)
                try:
                    user = await repository.get(session.get('user_id', ''))
                    if user.is_active and user.is_verified:
                        return user
                except UserNotFoundException:
                    return None
    return retrieve_user_handler
