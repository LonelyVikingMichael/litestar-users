from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Generic, Sequence, TypeVar

from jose import JWTError
from starlite.contrib.jwt.jwt_token import Token
from starlite.exceptions import ImproperlyConfiguredException

from starlite_users.adapter.sqlalchemy.mixins import (
    RoleModelType,
    SQLAlchemyRoleMixin,
    UserModelType,
)
from starlite_users.exceptions import (
    InvalidTokenException,
    RepositoryConflictException,
    RepositoryNotFoundException,
)
from starlite_users.password import PasswordManager
from starlite_users.schema import (
    RoleCreateDTOType,
    RoleUpdateDTOType,
    UserAuthSchema,
    UserCreateDTOType,
    UserUpdateDTOType,
)

__all__ = ["BaseUserService"]


if TYPE_CHECKING:
    from uuid import UUID

    from pydantic import SecretStr

    from starlite_users.adapter.sqlalchemy.repository import SQLAlchemyUserRepository


class BaseUserService(
    Generic[UserModelType, UserCreateDTOType, UserUpdateDTOType, RoleModelType]
):  # pylint: disable=R0904
    """Main user management interface."""

    user_model: type[UserModelType]
    """A subclass of the `User` ORM model."""

    def __init__(
        self,
        repository: SQLAlchemyUserRepository[UserModelType, RoleModelType],
        secret: SecretStr,
        hash_schemes: Sequence[str] | None = None,
    ) -> None:
        """User service constructor.

        Args:
            repository: A `UserRepository` instance
            secret: Secret string for securely signing tokens.
            hash_schemes: Schemes to use for password encryption.
        """
        self.repository = repository
        self.secret = secret
        self.password_manager = PasswordManager(hash_schemes=hash_schemes)
        self.user_model = self.repository.user_model
        self.role_model = self.repository.role_model

    async def add_user(self, data: UserCreateDTOType, process_unsafe_fields: bool = False) -> UserModelType:
        """Create a new user programmatically.

        Args:
            data: User creation data transfer object.
            process_unsafe_fields: If True, set `is_active` and `is_verified` attributes as they appear in `data`, otherwise always set their defaults.
        """
        try:
            existing_user = await self.get_user_by(email=data.email)
            if existing_user:
                raise RepositoryConflictException("email already associated with an account")
        except RepositoryNotFoundException:
            pass

        user_dict = data.dict(exclude={"password"}, exclude_unset=True)
        user_dict["password_hash"] = self.password_manager.hash(data.password)
        if not process_unsafe_fields:
            user_dict["is_verified"] = False
            user_dict["is_active"] = True

        return await self.repository.add_user(self.user_model(**user_dict))  # pyright: ignore

    async def register(self, data: UserCreateDTOType) -> UserModelType | None:
        """Register a new user and optionally run custom business logic.

        Args:
            data: User creation data transfer object.
        """
        if not await self.pre_registration_hook(data):
            return None

        user = await self.add_user(data)
        await self.initiate_verification(user)  # TODO: make verification optional?

        await self.post_registration_hook(user)

        return user

    async def get_user(self, id_: "UUID") -> UserModelType:
        """Retrieve a user from the database by id.

        Args:
            id_: UUID corresponding to a user primary key.
        """
        return await self.repository.get_user(id_)

    async def get_user_by(self, **kwargs: Any) -> UserModelType:
        """Retrieve a user from the database by arbitrary keyword arguments.

        Args:
            **kwargs: Keyword arguments to pass as filters.

        Examples:
            ```python
            service = UserService(...)
            john = await service.get_user_by(email="john@example.com")
            ```
        """
        return await self.repository.get_user_by(**kwargs)

    async def update_user(self, id_: "UUID", data: UserUpdateDTOType) -> UserModelType:
        """Update arbitrary user attributes in the database.

        Args:
            id_: UUID corresponding to a user primary key.
            data: User update data transfer object.
        """
        update_dict = data.dict(exclude={"password"}, exclude_unset=True)
        if data.password:
            update_dict["password_hash"] = self.password_manager.hash(data.password)

        return await self.repository.update_user(id_, update_dict)

    async def delete_user(self, id_: "UUID") -> None:
        """Delete a user from the database.

        Args:
            id_: UUID corresponding to a user primary key.
        """
        return await self.repository.delete_user(id_)

    async def authenticate(self, data: UserAuthSchema) -> UserModelType | None:
        """Authenticate a user.

        Args:
            data: User authentication data transfer object.
        """
        # avoid early returns to mitigate timing attacks.
        # check if user supplied logic should allow authentication, but only
        # supply the result later.
        should_proceed = await self.pre_login_hook(data)

        try:
            user = await self.repository.get_user_by(email=data.email)
        except RepositoryNotFoundException:
            self.password_manager.hash(data.password)
            return None

        password_verified, new_password_hash = self.password_manager.verify_and_update(
            data.password, user.password_hash
        )
        if new_password_hash is not None:
            user = await self.repository._update(user, {"password_hash": new_password_hash})

        if not password_verified or not should_proceed:
            return None

        await self.post_login_hook(user)

        return user

    def generate_token(self, user_id: "UUID", aud: str) -> str:
        """Generate a limited time valid JWT.

        Args:
            user_id: UUID of the user to provide the token to.
            aud: Context of the token
        """
        token = Token(
            exp=datetime.now() + timedelta(seconds=60 * 60 * 24),  # noqa: DTZ005
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
        await self.send_verification_token(user, token)

    async def send_verification_token(self, user: UserModelType, token: str) -> None:
        """Execute custom logic to send the verification token to the relevant user.

        Args:
            user: The user requesting verification.
            token: An encoded JWT bound to verification.

        Notes:
        - Develepors need to override this method to facilitate sending the token via email, sms etc.
        """

    async def verify(self, encoded_token: str) -> UserModelType:
        """Verify a user with the given JWT.

        Args:
            encoded_token: An encoded JWT bound to verification.

        Raises:
            InvalidTokenException: If the token is expired or tampered with.
        """
        token = self._decode_and_verify_token(encoded_token, context="verify")

        user_id = token.sub
        try:
            user = await self.repository.update_user(user_id, {"is_verified": True})
        except RepositoryNotFoundException as e:
            raise InvalidTokenException("token is invalid") from e

        await self.post_verification_hook(user)

        return user

    async def initiate_password_reset(self, email: str) -> None:
        """Initiate the password reset flow.

        Args:
            email: Email of the user who has forgotten their password.
        """
        try:
            user = await self.get_user_by(email=email)  # TODO: something about timing attacks.
        except RepositoryNotFoundException:
            return
        token = self.generate_token(user.id, aud="reset_password")
        await self.send_password_reset_token(user, token)

    async def send_password_reset_token(self, user: UserModelType, token: str) -> None:
        """Execute custom logic to send the password reset token to the relevant user.

        Args:
            user: The user requesting the password reset.
            token: An encoded JWT bound to the password reset flow.

        Notes:
        - Develepors need to override this method to facilitate sending the token via email, sms etc.
        """

    async def reset_password(self, encoded_token: str, password: "SecretStr") -> None:
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
            await self.repository.update_user(user_id, {"password_hash": self.password_manager.hash(password)})
        except RepositoryNotFoundException as e:
            raise InvalidTokenException from e

    async def pre_login_hook(self, data: UserAuthSchema) -> bool:  # pylint: disable=W0613
        """Execute custom logic to run custom business logic prior to authenticating a user.

        Useful for authentication checks against external sources,
        eg. current membership validity or blacklists, etc
        Must return `False` or raise a custom exception to cancel authentication.

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
        """Execute custom logic to run custom business logic after authenticating a user.

        Useful for eg. updating a login counter, updating last known user IP
        address, etc.

        Args:
            user: The user who has authenticated.

        Notes:
            Uncaught exceptions in this method will break the authentication process.
        """

    async def pre_registration_hook(self, data: UserCreateDTOType) -> bool:  # pylint: disable=W0613
        """Execute custom logic to run custom business logic prior to registering a user.

        Useful for authorization checks against external sources,
        eg. membership API or blacklists, etc.
        Must return `False` or raise a custom exception to cancel registration.

        Args:
            data: User creation data transfer object

        Returns:
            True: If registration should proceed
            False: If registration is not to proceed.

        Notes:
        - Uncaught exceptions in this method will result in failed registration attempts.
        """

        return True

    async def post_registration_hook(self, user: UserModelType) -> None:
        """Execute custom logic to run custom business logic after registering a user.

        Useful for updating external datasets, sending welcome messages etc.

        Args:
            user: User ORM instance.

        Notes:
        - Uncaught exceptions in this method could result in returning a HTTP 500 status
        code while successfully creating the user in the database.
        - It's possible to skip verification entirely by setting `user.is_verified`
        to `True` here.
        """

    async def post_verification_hook(self, user: UserModelType) -> None:
        """Execute custom logic to run custom business logic after a user has verified details.

        Useful for eg. updating sales lead data, etc.

        Args:
            user: User ORM instance.

        Notes:
        - Uncaught exceptions in this method could result in returning a HTTP 500 status
        code while successfully validating the user.
        """

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

    async def get_role(self, id_: "UUID") -> RoleModelType:
        """Retrieve a role by id.

        Args:
            id_: UUID of the role.
        """
        return await self.repository.get_role(id_)

    async def get_role_by_name(self, name: str) -> RoleModelType:
        """Retrieve a role by name.

        Args:
            name: The name of the role.
        """
        return await self.repository.get_role_by_name(name)

    async def add_role(self, data: RoleCreateDTOType) -> RoleModelType:
        """Add a new role to the database.

        Args:
            data: A role creation data transfer object.
        """
        if self.role_model is None or not issubclass(self.role_model, SQLAlchemyRoleMixin):
            raise ImproperlyConfiguredException("StarliteUsersConfig.role_model must subclass SQLAlchemyRoleMixin")
        return await self.repository.add_role(self.role_model(**data.dict()))  # pyright: ignore

    async def update_role(self, id_: "UUID", data: RoleUpdateDTOType) -> RoleModelType:
        """Update a role in the database.

        Args:
            id_: UUID corresponding to the role primary key.
            data: A role update data transfer object.
        """
        return await self.repository.update_role(id_, data.dict(exclude_unset=True))

    async def delete_role(self, id_: "UUID") -> None:
        """Delete a role from the database.

        Args:
            id_: UUID corresponding to the role primary key.
        """
        return await self.repository.delete_role(id_)

    async def assign_role_to_user(self, user_id: "UUID", role_id: "UUID") -> UserModelType:
        """Add a role to a user.

        Args:
            user_id: UUID of the user to receive the role.
            role_id: UUID of the role to add to the user.
        """
        user = await self.get_user(user_id)
        role = await self.get_role(role_id)

        if isinstance(user.roles, list) and role in user.roles:
            raise RepositoryConflictException(f"user already has role '{role.name}'")
        return await self.repository.assign_role_to_user(user, role)

    async def revoke_role_from_user(self, user_id: "UUID", role_id: "UUID") -> UserModelType:
        """Revoke a role from a user.

        Args:
            user_id: UUID of the user to revoke the role from.
            role_id: UUID of the role to revoke.
        """
        user = await self.get_user(user_id)
        role = await self.get_role(role_id)

        if isinstance(user.roles, list) and role not in user.roles:
            raise RepositoryConflictException(f"user does not have role '{role.name}'")
        return await self.repository.revoke_role_from_user(user, role)


UserServiceType = TypeVar("UserServiceType", bound=BaseUserService)
