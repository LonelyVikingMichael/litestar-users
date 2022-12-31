# Route handler configs

Starlite-Users will take care of registering the provided route handlers on the application if the relevant configurations are passed to `StarliteUsersConfig`.

All routes are configurable via these classes, though sensible defaults are provided in each case.

The following configurations (and route handlers, by extension) are available:

* [`AuthHandlerConfig`][starlite_users.config.AuthHandlerConfig] provides `login` and `logout` route handlers. Note that logout is not available on `JWT` auth backends.
* [`CurrentUserHandlerConfig`][starlite_users.config.CurrentUserHandlerConfig] provides `get_current_user` and `update_current_user1 route handlers.
* [`PasswordResetHandlerConfig`][starlite_users.config.PasswordResetHandlerConfig] provides `forgot_password` and `reset_password` route handlers.
* [`RegisterHandlerConfig`][starlite_users.config.RegisterHandlerConfig] provides the `register` (AKA signup) route handler. By default, newly registered users will require verification before they can login.
* [`RoleManagementHandlerConfig`][starlite_users.config.RoleManagementHandlerConfig] provides `create_role`, `update_role`, `delete_role`, `assign_role_to_user` and `revoke_role_from_user` route handlers. Requires `Role` database models and DTOs to be set up.
* [`UserManagementHandlerConfig`][starlite_users.config.UserManagementHandlerConfig] provides `get_user`, `update_user` and `delete_user` route handlers. Requires `Role` database models and DTOs to be set up.
* [`VerificationHandlerConfig`][starlite_users.config.VerificationHandlerConfig] provides the `verify` route handler.
