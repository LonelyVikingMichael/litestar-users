# User Schema

::: starlite_users.schema.BaseUserCreateDTO
    options:
        members:
            - email
            - password
            - is_active
            - is_verified

::: starlite_users.schema.BaseUserReadDTO
    options:
        members:
            - email
            - password
            - is_active
            - is_verified

::: starlite_users.schema.BaseUserUpdateDTO
    options:
        members:
            - email
            - password
            - is_active
            - is_verified
