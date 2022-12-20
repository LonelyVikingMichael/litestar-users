from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Generic, Optional, Type, TypeVar
from uuid import UUID

from jose import JWTError
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession
from starlite import ASGIConnection
from starlite.contrib.jwt.jwt_token import Token

from .adapter.sqlalchemy.models import RoleModelType, UserModelType
from .adapter.sqlalchemy.repository import SQLAlchemyUserRepository
from .exceptions import (
    InvalidTokenException,
    UserConflictException,
    UserNotFoundException,
)
from .password import PasswordManager
from .schema import UserAuthSchema, UserCreateDTOType, UserUpdateDTOType


class UserService(Generic[UserModelType, UserCreateDTOType, UserUpdateDTOType]):
    """Main user management interface."""

    user_model: Type[UserModelType]
    """
    A subclass of a `User` ORM model.
    """
    secret: SecretStr
    """
    Secret string for securely signing tokens.
    """

    def __init__(self, repository: SQLAlchemyUserRepository) -> None:
        """User service constructor.

        Args:
            repository: A `UserRepository` instance
        """
        self.repository = repository
        self.password_manager = PasswordManager()

    async def add(self, data: UserCreateDTOType, process_unsafe_fields: bool = False) -> UserModelType:
        """Create a new user programatically.

        Args:
            data: User creation data transfer object.
            process_unsafe_fields: If True, set `is_active` and `is_verified` attributes as they appear in `data`, otherwise always set their defaults.
        """
        try:
            existing_user = await self.get_by(email=data.email)
            if existing_user:
                raise UserConflictException("email already associated with an account")
        except UserNotFoundException:
            pass

        user_dict = data.dict(exclude={"password"})
        user_dict["password_hash"] = self.password_manager.get_hash(data.password)
        if not process_unsafe_fields:
            user_dict["is_verified"] = False
            user_dict["is_active"] = True

        user = await self.repository.add(self.user_model(**user_dict))

        return user

    async def register(self, data: UserCreateDTOType) -> UserModelType:
        """Register a new user and optionally run custom business logic.

        Args:
            data: User creation data transfer object.
        """
        await self.pre_registration_hook(data)

        user = await self.add(data)
        await self.initiate_verification(user)  # TODO: make verification optional?

        await self.post_registration_hook(user)

        return user

    async def get(self, id_: UUID) -> UserModelType:
        """Retrieve a user from the database by id.

        Args:
            id_: UUID corresponding to a user primary key.
        """
        return await self.repository.get(id_)

    async def get_by(self, **kwargs) -> UserModelType:
        """Retrieve a user from the database by arbitrary keyword arguments.

        Args:
            **kwargs: Keyword arguments to pass as filters.

        Examples:
            ```python
            repository = UserService(...)
            john = await service.get_by(email='john@example.com')
            ```
        """
        return await self.repository.get_by(**kwargs)

    async def update(self, id_: UUID, data: UserUpdateDTOType) -> UserModelType:
        """Update arbitrary user attributes in the database.

        Args:
            id_: UUID corresponding to a user primary key.
            data: Dictionary to map to user columns and values.
        """
        update_dict = data.dict(exclude={"password"}, exclude_unset=True)
        if data.password:
            update_dict["password_hash"] = self.password_manager.get_hash(data.password)

        return await self.repository.update(id_, update_dict)

    async def delete(self, id_: UUID) -> None:
        """Delete a user from the database.

        Args:
            id_: UUID corresponding to a user primary key.
        """
        return await self.repository.delete(id_)

    async def authenticate(self, data: UserAuthSchema) -> Optional[UserModelType]:
        """Authenticate a user.

        Args:
            data: User authentication data transfer object.
        """
        if not await self.pre_login_hook(data):
            return

        user = await self.repository.get_by(email=data.email)
        if user is None:
            return

        verified, new_password_hash = self.password_manager.verify_and_update(data.password, user.password_hash)
        if not verified:
            return
        if new_password_hash is not None:
            user = await self.repository._update(user, {"password_hash": new_password_hash})

        await self.post_login_hook(user)

        return user

    def generate_token(self, user_id: UUID, aud: str) -> str:
        """Generate a limited time valid JWT.

        Args:
            user_id: UUID of the user to provide the token to.
            aud: Context of the token
        """
        token = Token(
            exp=datetime.now() + timedelta(seconds=60 * 60 * 24),  # TODO: make time configurable?
            sub=str(user_id),
            aud=aud,
        )
        return token.encode(secret=self.secret.get_secret_value(), algorithm="HS256")

    async def initiate_verification(self, user: UserModelType) -> None:
        """Initiate the user verification flow.

        Args:
            user: The user requesting verification.
        """
        token = self.generate_token(user.id, aud="verify")
        await self.send_verifification_token(user, token)

    async def send_verifification_token(self, user: UserModelType, token: str) -> None:
        """Hook to send the verification token to the relevant user.

        Args:
            user: The user requesting verification.
            token: An encoded JWT bound to verification.

        Notes:
        - Develepors need to override this method to facilitate sending the token via email, sms etc.
        """

        pass

    async def verify(self, encoded_token: str) -> None:
        """Verify a user with the given JWT.

        Args:
            token: An encoded JWT bound to verification.

        Raises:
            InvalidTokenException: If the token is expired or tampered with.
        """
        token = self._decode_and_verify_token(encoded_token, context="verify")

        user_id = token.sub
        try:
            user = await self.repository.update(user_id, {"is_verified": True})
        except UserNotFoundException as e:
            raise InvalidTokenException from e

        await self.post_verification_hook(user)

        return user

    async def initiate_password_reset(self, email: str) -> None:
        """Initiate the password reset flow.

        Args:
            email: Email of the user who has forgotten their password.
        """
        try:
            user = await self.get_by(email=email)  # TODO: something about timing attacks.
        except UserNotFoundException:
            return
        token = self.generate_token(user.id, aud="reset_password")
        await self.send_password_reset_token(user, token)

    async def send_password_reset_token(self, user: UserModelType, token: str) -> None:
        """Hook to send the password reset token to the relevant user.

        Args:
            user: The user requesting the password reset.
            token: An encoded JWT bound to the password reset flow.

        Notes:
        - Develepors need to override this method to facilitate sending the token via email, sms etc.
        """

        pass

    async def reset_password(self, encoded_token: str, password: SecretStr) -> None:
        """Reset a user's password given a valid JWT.

        Args:
            encoded_token: An encoded JWT bound to the password reset flow.
            password: The new password to hash and store.

        Raises:
            InvalidTokenException: If the token has expired or been tampered with.
        """
        token = self._decode_and_verify_token(encoded_token, context="reset_password")

        user_id = token.sub
        try:
            await self.repository.update(user_id, {"password_hash": self.password_manager.get_hash(password)})
        except UserNotFoundException as e:
            raise InvalidTokenException from e

    async def pre_login_hook(self, data: UserAuthSchema) -> bool:
        """Hook to run custom business logic prior to authenticating a user.

        Useful for authorization checks agains external sources,
        eg. current membership validity or blacklists, etc

        Args:
            data: Authentication data transfer object.

        Returns:
            True: If authentication should proceed
            False: If authentication is not to proceed.

        Notes:
            Uncaught exceptions in this method will break the authentication process.
        """

        return True

    async def post_login_hook(self, user: UserModelType) -> None:
        """Hook to run custom business logic after authenticating a user.

        Useful for eg. updating a login counter, updating last known user IP
        address, etc.

        Args:
            user: The user who has authenticated.

        Notes:
            Uncaught exceptions in this method will break the authentication process.
        """

        pass

    async def pre_registration_hook(self, data: UserCreateDTOType) -> None:
        """Hook to run custom business logic prior to registering a user.

        Useful for authorization checks against external sources,
        eg. membership API or blacklists, etc.

        Args:
            data: User creation data transfer object

        Notes:
        - Uncaught exceptions in this method will result in failed registration attempts.
        """

        pass

    async def post_registration_hook(self, user: UserModelType) -> None:
        """Hook to run custom business logic after registering a user.

        Useful for updating external datasets, sending welcome messages etc.

        Args:
            user: User ORM instance.

        Notes:
        - Uncaught exceptions in this method could result in returning a HTTP 500 status
        code while successfully creating the user in the database.
        - It's possible to skip verification entirely by setting `user.is_verified`
        to `True` here.
        """

        pass

    async def post_verification_hook(self, user: UserModelType):
        """Hook to run custom business logic after a user has verified details.

        Useful for eg. updating sales lead data, etc.

        Args:
            user: User ORM instance.

        Notes:
        - Uncaught exceptions in this method could result in returning a HTTP 500 status
        code while successfully validating the user.
        """

        pass

    def _decode_and_verify_token(self, encoded_token: str, context: str) -> Token:
        try:
            token = Token.decode(
                encoded_token=encoded_token,
                secret=self.secret.get_secret_value(),
                algorithm="HS256",
            )
        except JWTError as e:
            raise InvalidTokenException from e

        if token.aud != context:
            raise InvalidTokenException(f"aud value must be {context}")

        return token


def get_session_retrieve_user_handler(user_model: Type[UserModelType], role_model: Type[RoleModelType]) -> Callable:
    """Factory to get retrieve_user_handler functions for session backends.

    Args:
        user_model: A subclass of a `User` ORM model.
    """

    async def retrieve_user_handler(session: Dict[str, Any], connection: ASGIConnection) -> Optional[user_model]:
        """Handler to register with a Starlite auth backend, specific to SQLAlchemy.

        Args:
            session: Starlite session
        """
        async_session_maker = connection.app.state.session_maker_class

        async with async_session_maker() as async_session:
            async with async_session.begin():
                repository = SQLAlchemyUserRepository(
                    session=async_session, user_model_type=user_model, role_model_type=role_model
                )
                try:
                    user = await repository.get(session.get("user_id", ""))
                    if user.is_active and user.is_verified:
                        return user
                except UserNotFoundException:
                    return None

    return retrieve_user_handler


def get_jwt_retrieve_user_handler(user_model: Type[UserModelType], role_model: Type[RoleModelType]) -> Callable:
    """Factory to get retrieve_user_handler functions for jwt backends.

    Args:
        user_model: A subclass of a `User` ORM model.
    """

    async def retrieve_user_handler(token: Token, connection: ASGIConnection[Any, Any, Any]) -> Optional[user_model]:
        """Handler to register with a Starlite auth backend, specific to SQLAlchemy.

        Args:
            token: Encoded JWT
        """
        async_session_maker = connection.app.state.session_maker_class

        async with async_session_maker() as async_session:
            async with async_session.begin():
                repository = SQLAlchemyUserRepository(
                    session=async_session, user_model_type=user_model, role_model_type=role_model
                )
                try:
                    user = await repository.get(token.sub)
                    if user.is_active and user.is_verified:
                        return user
                except UserNotFoundException:
                    return None

    return retrieve_user_handler


UserServiceType = TypeVar("UserServiceType", bound=UserService)


def get_service_dependency(
    user_model: Type[UserModelType], role_model: Type[RoleModelType], user_service_class: Type[UserServiceType]
):
    """Factory to get service dependencies.

    Args:
        user_model: A subclass of a `User` ORM model.
        user_service_class: A subclass of [UserService][starlite_users.service.UserService]
    """

    def get_service(session: AsyncSession) -> UserServiceType:
        """Instantiate service and repository for use with DI.

        Args:
            session: SQLAlchemy AsyncSession
        """
        return user_service_class(
            SQLAlchemyUserRepository(session=session, user_model_type=user_model, role_model_type=role_model)
        )

    return get_service
