# Role Schema

::: starlite_users.schema.BaseRoleCreateDTO
    options:
        members:
            - name
            - description

::: starlite_users.schema.BaseRoleReadDTO
    options:
        members:
            - id
            - name
            - description

::: starlite_users.schema.BaseRoleUpdateDTO
    options:
        members:
            - name
            - description
