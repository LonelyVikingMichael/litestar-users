# Route handler configs

Starlite-Users will take care of registering the provided route handlers on the application if the relevant configurations are passed to `StarliteUsersConfig`.

All routes are configurable via these classes, though sensible defaults are provided in each case.

The following configurations (and route handlers, by extension) are available:

* [`AuthHandlerConfig`][starlite_users.config.AuthHandlerConfig] provides the following route handlers:
  * `login`: Allows users to authenticate.
  * `logout`: Allows authenticated users to logout. Not available when the authentication backend is JWT based.
* [`CurrentUserHandlerConfig`][starlite_users.config.CurrentUserHandlerConfig] provides the following route handlers:
  * `get_current_user`: Get info on the currently authenticated user.
  * `update_current_user`: Update the currently authenticated user's info.
* [`PasswordResetHandlerConfig`][starlite_users.config.PasswordResetHandlerConfig] provides the following route handlers:
  * `forgot_password`: Inititiates the password reset flow. Always returns a HTTP 2XX status code.
  * `reset_password`: Reset a user's password, given a valid reset token.
* [`RegisterHandlerConfig`][starlite_users.config.RegisterHandlerConfig] provides the following route handlers:
  * `register` (aka signup). By default, newly registered users will need to verify their account before they can proceed to login.
* [`RoleManagementHandlerConfig`][starlite_users.config.RoleManagementHandlerConfig] requires `Role` database models and DTOs to be set up and provides the following route handlers:
  * `create_role`: Create a new role.
  * `update_role`: Update a role.
  * `delete_role`: Delete a role from the database.
  * `assign_role_to_user`: Assign an existing role to an existing user.
  * `revoke_role_from_user`: Revoke an existing role from an existing user.
* [`UserManagementHandlerConfig`][starlite_users.config.UserManagementHandlerConfig] requires `Role` database models and DTOs to be set up and provides the following route handlers:
  * `get_user`: Get a user's info.
  * `update_user`: Update a user's info.
  * `delete_user`: Delete a user from the database
* [`VerificationHandlerConfig`][starlite_users.config.VerificationHandlerConfig] provides the following route handler:
  * `verify`: Update a user's `is_verified` status to `True`, given a valid token.
