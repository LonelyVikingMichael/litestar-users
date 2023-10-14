from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import anyio
from click import argument, echo, group, option
from litestar.cli._utils import LitestarGroup

from litestar_users.utils import async_session, get_litestar_users_plugin, get_user_service

if TYPE_CHECKING:
    from litestar import Litestar


@group(cls=LitestarGroup, name="users")
def user_management_group() -> None:
    """Manage users."""


@user_management_group.command(
    name="create-user",
    help="Create a new user in the database.",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@argument("email")
@argument("password")
@option("--is_active", is_flag=True, default=True, type=bool, help="Set the user as active.")
@option("--is_verified", is_flag=True, default=True, type=bool, help="Set the user as verified.")
@option("--id", "id_", help="Set the user ID.")
@option("--bool", "-b", "booleans", multiple=True, help="Set one or more boolean attributes.")
@option("--int", "-i", "integers", multiple=True, help="Set one or more integer attributes.")
@option("--float", "-f", "floats", multiple=True, help="Set one or more float attributes.")
@option("--str", "-s", "strings", multiple=True, help="Set one or more string attributes.")
def create_user(
    app: Litestar,
    email: str,
    password: str,
    is_active: bool,
    is_verified: bool,
    id_: str | None,
    booleans: tuple[str],
    integers: tuple[str],
    floats: tuple[str],
    strings: tuple[str],
) -> None:
    """Create a new user in the database."""
    kwargs: dict[str, str | int | float | bool] = {}
    kwargs.update(
        {key: value.lower() in ("1", "true", "t", "yes", "y") for arg in booleans for key, value in [arg.split("=")]}
    )
    kwargs.update({key: int(value) for arg in integers for key, value in [arg.split("=")]})
    kwargs.update({key: float(value) for arg in floats for key, value in [arg.split("=")]})
    kwargs.update({key: value for arg in strings for key, value in [arg.split("=")]})
    if id_:
        kwargs["id"] = int(id_) if id_.isnumeric() else id_

    litestar_users_config = get_litestar_users_plugin(app)._config

    async def _create_user() -> None:
        async with async_session(app) as session:
            user_service = get_user_service(app, session)
            password_hash = user_service.password_manager.hash(password)
            user = await user_service.add_user(
                user=litestar_users_config.user_model(email=email, password_hash=password_hash, **kwargs),
                activate=is_active,
                verify=is_verified,
            )
            await session.commit()
            echo(f"User {user.id} created successfully.")

    anyio.run(_create_user)


@user_management_group.command(name="create-role", help="Create a new role in the database.")
@argument("name")
@argument("description", required=False)
def create_role(name: str, description: str | None, app: Litestar) -> None:
    """Create a new role in the database."""

    litestar_users_config = get_litestar_users_plugin(app)._config

    async def _create_role() -> None:
        async with async_session(app) as session:
            user_service = get_user_service(app, session)
            if litestar_users_config.role_model is None:
                echo("Role model is not defined")
                sys.exit(1)
            role = await user_service.add_role(litestar_users_config.role_model(name=name, description=description))
            await session.commit()
        echo(f"Role {role.id} created successfully.")

    anyio.run(_create_role)


@user_management_group.command(name="assign-role", help="Assign a role to a user.")
@argument("email")
@argument("role_name")
def assign_role(email: str, role_name: str, app: Litestar) -> None:
    """Assign a role to a user."""

    litestar_users_config = get_litestar_users_plugin(app)._config
    if litestar_users_config.role_model is None:
        echo("Role model is not defined")
        sys.exit(1)

    async def _assign_role() -> None:
        async with async_session(app) as session:
            user_service = get_user_service(app, session)
            user = await user_service.get_user_by(email=email)
            role = await user_service.get_role_by_name(role_name)
            await user_service.assign_role(user.id, role.id)  # type: ignore[union-attr]
        echo(f"Role {role_name} assigned to user {email} successfully.")

    anyio.run(_assign_role)


if __name__ == "__main__":
    from examples.basic import app

    create_user(app, "john.quincy.adams@examplepetstore.com", "password")
