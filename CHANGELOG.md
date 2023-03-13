# Changelog

[0.4.0]

- unify `BaseUserService` and `BaseUserRoleService` et al.
- add configuration options to `StarliteUsersConfig`.
- add `hash_schemes` configuration to `PasswordManager`
- remove configuration class variables from `BaseUserService`.
- remove `UserRoleAssociationMixin`.
- remove `SQLAlchemyUserRoleMixin`.
- remove `__tablename__` declarations from SQLAlchemy mixins.

[0.3.3]

- fix session login response serialization issue.

[0.3.2]

- fix verification issue.

[0.3.1]

- replace broken SQLAlchemy forward refs.

[0.3.0]

- add `BaseUserRoleService`
- add `BaseUserRoleReadDTO`
- add `SQLAlchemyUserRoleRepository`
- add `SQLAlchemyUserRolesMixin`
- remove `role` based methods from `BaseUserService`
- remove `role` based methods from `SQLAlchemyUserRepository`
- remove `roles` attribute from `BaseUserReadDTO`
- remove `roles` attribute from `SQLAlchemyUserMixin`
- update `get_service` dependency function.
- update `retrieve_user_handler` helpers.
- update examples.

[0.2.0]

- fix static type and linting errors.
- fix documentation issues.
- update route handler authorization guards to be generic.

[0.1.0]

- initial release.
