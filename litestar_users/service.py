from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Generic, Sequence, TypeVar
from uuid import UUID

from advanced_alchemy.exceptions import ConflictError, NotFoundError
from jose import JWTError
from litestar.contrib.jwt.jwt_token import Token
from litestar.exceptions import ImproperlyConfiguredException

from litestar_users.adapter.sqlalchemy.protocols import SQLARoleT, SQLAUserT
from litestar_users.exceptions import InvalidTokenException
from litestar_users.password import PasswordManager

__all__ = ["BaseUserService"]


if TYPE_CHECKING:
    from litestar import Request

    from litestar_users.adapter.sqlalchemy.repository import SQLAlchemyRoleRepository, SQLAlchemyUserRepository
    from litestar_users.schema import AuthenticationSchema


class BaseUserService(Generic[SQLAUserT, SQLARoleT]):  # pylint: disable=R0904
    """Main user management interface."""

    user_model: type[SQLAUserT]
    """A subclass of the `User` ORM model."""

    def __init__(
        self,
        secret: str,
        user_auth_identifier: str,
        user_repository: SQLAlchemyUserRepository[SQLAUserT],
        hash_schemes: Sequence[str] | None = None,
        role_repository: SQLAlchemyRoleRepository[SQLARoleT, SQLAUserT] | None = None,
    ) -> None:
        """User service constructor.

        Args:
            secret: Secret string for securely signing tokens.
            user_auth_identifier: The `User` model attribute to identify the user during authorization.
            user_repository: A `UserRepository` instance.
            hash_schemes: Schemes to use for password encryption.
            role_repository: A `RoleRepository` instance.
        """
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.secret = secret
        self.password_manager = PasswordManager(hash_schemes=hash_schemes)
        self.user_model = self.user_repository.model_type
        if role_repository is not None:
            self.role_model = role_repository.model_type
        self.user_auth_identifier = user_auth_identifier

    async def add_user(self, user: SQLAUserT, verify: bool = False, activate: bool = True) -> SQLAUserT:
        """Create a new user programmatically.

        Args:
            user: User model instance.
            verify: Set the user's verification status to this value.
            activate: Set the user's active status to this value.
        """
        existing_user = await self.get_user_by(email=user.email)
        if existing_user:
            raise ConflictError("email already associated with an account")

        user.is_verified = verify
        user.is_active = activate

        return await self.user_repository.add(user)

    async def register(self, data: dict[str, Any], request: Request | None = None) -> SQLAUserT:
        """Register a new user and optionally run custom business logic.

        Args:
            data: User creation data transfer object.
            request: The litestar request that initiated the action.
        """
        await self.pre_registration_hook(data, request)

        data["password_hash"] = self.password_manager.hash(data.pop("password"))
        user = await self.add_user(self.user_model(**data))  # type: ignore[arg-type]
        await self.initiate_verification(user)  # TODO: make verification optional?

        await self.post_registration_hook(user, request)

        return user

    async def get_user(self, id_: UUID | int) -> SQLAUserT:
        """Retrieve a user from the database by id.

        Args:
            id_: UUID corresponding to a user primary key.
        """
        return await self.user_repository.get(id_)

    async def get_user_by(self, **kwargs: Any) -> SQLAUserT | None:
        """Retrieve a user from the database by arbitrary keyword arguments.

        Args:
            **kwargs: Keyword arguments to pass as filters.

        Examples:
            ```python
            service = UserService(...)
            john = await service.get_one(email="john@example.com")
            ```
        """
        return await self.user_repository.get_one_or_none(**kwargs)

    async def update_user(self, data: SQLAUserT) -> SQLAUserT:
        """Update arbitrary user attributes in the database.

        Args:
            data: User update data transfer object.
        """

        return await self.user_repository.update(data)

    async def delete_user(self, id_: UUID | int) -> SQLAUserT:
        """Delete a user from the database.

        Args:
            id_: UUID corresponding to a user primary key.
        """
        return await self.user_repository.delete(id_)

    async def authenticate(self, data: Any, request: Request | None = None) -> SQLAUserT | None:
        """Authenticate a user.

        Args:
            data: User authentication data transfer object.
            request: The litestar request that initiated the action.
        """
        # avoid early returns to mitigate timing attacks.
        # check if user supplied logic should allow authentication, but only
        # supply the result later.
        should_proceed = await self.pre_login_hook(data, request)

        try:
            user = await self.user_repository.get_one(
                **{self.user_auth_identifier: getattr(data, self.user_auth_identifier)}
            )
        except NotFoundError:
            # trigger passlib's `dummy_verify` method
            self.password_manager.verify_and_update(data.password, None)
            return None

        password_verified, new_password_hash = self.password_manager.verify_and_update(
            data.password, user.password_hash
        )
        if new_password_hash is not None:
            user = await self.user_repository._update(user, {"password_hash": new_password_hash})

        if not password_verified or not should_proceed:
            return None

        await self.post_login_hook(user, request)

        return user

    def generate_token(self, user_id: UUID | int, aud: str) -> str:
        """Generate a limited time valid JWT.

        Args:
            user_id: ID of the user to provide the token to.
            aud: Context of the token
        """
        token = Token(
            exp=datetime.now() + timedelta(seconds=60 * 60 * 24),  # noqa: DTZ005
            sub=str(user_id),
            aud=aud,
        )
        return token.encode(secret=self.secret, algorithm="HS256")

    async def initiate_verification(self, user: SQLAUserT) -> None:
        """Initiate the user verification flow.

        Args:
            user: The user requesting verification.
        """
        token = self.generate_token(user.id, aud="verify")
        await self.send_verification_token(user, token)

    async def send_verification_token(self, user: SQLAUserT, token: str) -> None:
        """Execute custom logic to send the verification token to the relevant user.

        Args:
            user: The user requesting verification.
            token: An encoded JWT bound to verification.

        Notes:
        - Develepors need to override this method to facilitate sending the token via email, sms etc.
        """

    async def verify(self, encoded_token: str, request: Request | None = None) -> SQLAUserT:
        """Verify a user with the given JWT.

        Args:
            encoded_token: An encoded JWT bound to verification.
            request: The litestar request that initiated the action.

        Raises:
            InvalidTokenException: If the token is expired or tampered with.
        """
        token = self._decode_and_verify_token(encoded_token, context="verify")

        try:
            user_id: UUID | int = UUID(token.sub)
        except ValueError:
            user_id = int(token.sub)
        try:
            user = await self.user_repository.update(self.user_model(id=user_id, is_verified=True))  # type: ignore[arg-type]
        except NotFoundError as e:
            raise InvalidTokenException("token is invalid") from e

        await self.post_verification_hook(user, request)

        return user

    async def initiate_password_reset(self, email: str) -> None:
        """Initiate the password reset flow.

        Args:
            email: Email of the user who has forgotten their password.
        """
        user = await self.get_user_by(email=email)  # TODO: something about timing attacks.
        if user is None:
            return
        token = self.generate_token(user.id, aud="reset_password")
        await self.send_password_reset_token(user, token)

    async def send_password_reset_token(self, user: SQLAUserT, token: str) -> None:
        """Execute custom logic to send the password reset token to the relevant user.

        Args:
            user: The user requesting the password reset.
            token: An encoded JWT bound to the password reset flow.

        Notes:
        - Develepors need to override this method to facilitate sending the token via email, sms etc.
        """

    async def reset_password(self, encoded_token: str, password: str) -> None:
        """Reset a user's password given a valid JWT.

        Args:
            encoded_token: An encoded JWT bound to the password reset flow.
            password: The new password to hash and store.

        Raises:
            InvalidTokenException: If the token has expired or been tampered with.
        """
        token = self._decode_and_verify_token(encoded_token, context="reset_password")

        try:
            user_id: UUID | int = UUID(token.sub)
        except ValueError:
            user_id = int(token.sub)
        try:
            await self.user_repository.update(
                self.user_model(id=user_id, password_hash=self.password_manager.hash(password))  # type: ignore[arg-type]
            )
        except NotFoundError as e:
            raise InvalidTokenException from e

    async def pre_login_hook(
        self, data: AuthenticationSchema, request: Request | None = None
    ) -> bool:  # pylint: disable=W0613
        """Execute custom logic to run custom business logic prior to authenticating a user.

        Useful for authentication checks against external sources,
        eg. current membership validity or blacklists, etc
        Must return `False` or raise a custom exception to cancel authentication.

        Args:
            data: Authentication data transfer object.
            request: The litestar request that initiated the action.

        Notes:
            Uncaught exceptions in this method will break the authentication process.
        """
        return True

    async def post_login_hook(self, user: SQLAUserT, request: Request | None = None) -> None:
        """Execute custom logic to run custom business logic after authenticating a user.

        Useful for eg. updating a login counter, updating last known user IP
        address, etc.

        Args:
            user: The user who has authenticated.
            request: The litestar request that initiated the action.

        Notes:
            Uncaught exceptions in this method will break the authentication process.
        """
        return

    async def pre_registration_hook(
        self, data: dict[str, Any], request: Request | None = None
    ) -> None:  # pylint: disable=W0613
        """Execute custom logic to run custom business logic prior to registering a user.

        Useful for authorization checks against external sources,
        eg. membership API or blacklists, etc.

        Args:
            data: User creation data transfer object
            request: The litestar request that initiated the action.

        Notes:
        - Uncaught exceptions in this method will result in failed registration attempts.
        """
        return

    async def post_registration_hook(self, user: SQLAUserT, request: Request | None = None) -> None:
        """Execute custom logic to run custom business logic after registering a user.

        Useful for updating external datasets, sending welcome messages etc.

        Args:
            user: User ORM instance.
            request: The litestar request that initiated the action.

        Notes:
        - Uncaught exceptions in this method could result in returning a HTTP 500 status
        code while successfully creating the user in the database.
        - It's possible to skip verification entirely by setting `user.is_verified`
        to `True` here.
        """
        return

    async def post_verification_hook(self, user: SQLAUserT, request: Request | None = None) -> None:
        """Execute custom logic to run custom business logic after a user has verified details.

        Useful for eg. updating sales lead data, etc.

        Args:
            user: User ORM instance.
            request: The litestar request that initiated the action.

        Notes:
        - Uncaught exceptions in this method could result in returning a HTTP 500 status
        code while successfully validating the user.
        """
        return

    def _decode_and_verify_token(self, encoded_token: str, context: str) -> Token:
        try:
            token = Token.decode(
                encoded_token=encoded_token,
                secret=self.secret,
                algorithm="HS256",
            )
        except JWTError as e:
            raise InvalidTokenException from e

        if token.aud != context:
            raise InvalidTokenException(f"aud value must be {context}")

        return token

    async def get_role(self, id_: UUID | int) -> SQLARoleT:
        """Retrieve a role by id.

        Args:
            id_: ID of the role.
        """
        if self.role_repository is None:
            raise ImproperlyConfiguredException("roles have not been configured")
        return await self.role_repository.get(id_)

    async def get_role_by_name(self, name: str) -> SQLARoleT:
        """Retrieve a role by name.

        Args:
            name: The name of the role.
        """
        if self.role_repository is None:
            raise ImproperlyConfiguredException("roles have not been configured")
        return await self.role_repository.get_one(name=name)

    async def add_role(self, data: SQLARoleT) -> SQLARoleT:
        """Add a new role to the database.

        Args:
            data: A role creation data transfer object.
        """
        if self.role_repository is None:
            raise ImproperlyConfiguredException("roles have not been configured")
        return await self.role_repository.add(data)

    async def update_role(self, id_: UUID | int, data: SQLARoleT) -> SQLARoleT:
        """Update a role in the database.

        Args:
            id_: UUID corresponding to the role primary key.
            data: A role update data transfer object.
        """
        if self.role_repository is None:
            raise ImproperlyConfiguredException("roles have not been configured")
        return await self.role_repository.update(data)

    async def delete_role(self, id_: UUID | int) -> SQLARoleT:
        """Delete a role from the database.

        Args:
            id_: UUID corresponding to the role primary key.
        """
        if self.role_repository is None:
            raise ImproperlyConfiguredException("roles have not been configured")
        return await self.role_repository.delete(id_)

    async def assign_role(self, user_id: UUID | int, role_id: UUID | int) -> SQLAUserT:
        """Add a role to a user.

        Args:
            user_id: ID of the user to receive the role.
            role_id: ID of the role to add to the user.
        """
        if self.role_repository is None:
            raise ImproperlyConfiguredException("roles have not been configured")
        user = await self.get_user(user_id)
        role = await self.get_role(role_id)

        if not hasattr(user, "roles"):
            raise ImproperlyConfiguredException("roles have not been configured")

        if isinstance(user.roles, list) and role in user.roles:  # pyright: ignore
            raise ConflictError(f"user already has role '{role.name}'")
        return await self.role_repository.assign_role(user, role)

    async def revoke_role(self, user_id: UUID | int, role_id: UUID | int) -> SQLAUserT:
        """Revoke a role from a user.

        Args:
            user_id: ID of the user to revoke the role from.
            role_id: ID of the role to revoke.
        """
        if self.role_repository is None:
            raise ImproperlyConfiguredException("roles have not been configured")
        user = await self.get_user(user_id)
        role = await self.get_role(role_id)

        if not hasattr(user, "roles"):
            raise ImproperlyConfiguredException("roles have not been configured")

        if isinstance(user.roles, list) and role not in user.roles:  # pyright: ignore
            raise ConflictError(f"user does not have role '{role.name}'")
        return await self.role_repository.revoke_role(user, role)


UserServiceType = TypeVar("UserServiceType", bound=BaseUserService)
