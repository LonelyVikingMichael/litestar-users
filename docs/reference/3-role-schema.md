# Role Schema

::: litestar_users.schema.BaseRoleCreateDTO
    options:
        members:
            - name
            - description

::: litestar_users.schema.BaseRoleReadDTO
    options:
        members:
            - id
            - name
            - description

::: litestar_users.schema.BaseRoleUpdateDTO
    options:
        members:
            - name
            - description
