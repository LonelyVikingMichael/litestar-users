# Route Handler Configurations

::: starlite_users.config.AuthHandlerConfig
    options:
        members:
            - login_path
            - logout_path

::: starlite_users.config.CurrentUserHandlerConfig
    options:
        members:
            - path

::: starlite_users.config.PasswordResetHandlerConfig
    options:
        members:
            - forgot_path
            - reset_path

::: starlite_users.config.RegisterHandlerConfig
    options:
        members:
            - path

::: starlite_users.config.RoleManagementHandlerConfig
    options:
        members:
            - path_prefix
            - assign_role_path
            - revoke_role_path
            - authorized_roles

::: starlite_users.config.UserManagementHandlerConfig
    options:
        members:
            - path_prefix
            - authorized_roles

::: starlite_users.config.VerificationHandlerConfig
    options:
        members:
            - path
