# User Schema

::: litestar_users.schema.BaseUserCreateDTO
    options:
        members:
            - email
            - password
            - is_active
            - is_verified

::: litestar_users.schema.BaseUserReadDTO
    options:
        members:
            - email
            - password
            - is_active
            - is_verified

::: litestar_users.schema.BaseUserUpdateDTO
    options:
        members:
            - email
            - password
            - is_active
            - is_verified

::: litestar_users.schema.BaseUserRoleReadDTO
    options:
        members:
            - email
            - password
            - is_active
            - is_verified
            - roles
