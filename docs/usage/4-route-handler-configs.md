# Route handler configs

Litestar-Users will take care of registering the provided route handlers on the application if the relevant configurations are passed to `LitestarUsersConfig`.

All routes are configurable via these classes, though sensible defaults are provided in each case.

The following configurations (and route handlers, by extension) are available:

## [`AuthHandlerConfig`][litestar_users.config.AuthHandlerConfig]

Provides the following route handlers:

* `login`: Allows users to authenticate.
* `logout`: Allows authenticated users to logout. Not available when the authentication backend is JWT based.

## [`CurrentUserHandlerConfig`][litestar_users.config.CurrentUserHandlerConfig]

Provides the following route handlers:

* `get_current_user`: Get info on the currently authenticated user.
* `update_current_user`: Update the currently authenticated user's info.

## [`PasswordResetHandlerConfig`][litestar_users.config.PasswordResetHandlerConfig]

Provides the following route handlers:

* `forgot_password`: Inititiates the password reset flow. Always returns a HTTP 2XX status code.
* `reset_password`: Reset a user's password, given a valid reset token.

## [`RegisterHandlerConfig`][litestar_users.config.RegisterHandlerConfig]

Provides the following route handlers:

* `register` (aka signup). By default, newly registered users will need to verify their account before they can proceed to login.

## [`RoleManagementHandlerConfig`][litestar_users.config.RoleManagementHandlerConfig]

Provides the following route handlers:

* `create_role`: Create a new role.
* `update_role`: Update a role.
* `delete_role`: Delete a role from the database.
* `assign_role`: Assign an existing role to an existing user.
* `revoke_role`: Revoke an existing role from an existing user.

## [`UserManagementHandlerConfig`][litestar_users.config.UserManagementHandlerConfig]

Provides the following route handlers:

* `get_user`: Get a user's info.
* `update_user`: Update a user's info.
* `delete_user`: Delete a user from the database

## [`VerificationHandlerConfig`][litestar_users.config.VerificationHandlerConfig]

Provides the following route handlers:

* `verify`: Update a user's `is_verified` status to `True`, given a valid token.
