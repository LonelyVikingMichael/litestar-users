# Command line interface

Litestar Users provides a command line interface (CLI) to conveniently set up initial users in the database. It is built on top of the Litestar CLI API, and as such uses the `litestar` command as the main entrypoint. See Litestar CLI [documentation](https://docs.litestar.dev/latest/usage/cli.html) for more details.

## Commands

## **create-user**

Create a new user in the database.

### `litestar users create-user [OPTIONS]`

Options

**`--email <email>`**

The user's email address.

**`--password <password>`**

The user's login password.

**`--is_verified`**

Set the user as being verified.

**`--is_active`**

Set the user as active.

**`--id <id>`**

The user ID.

**`-b, --bool-attrs <key=value>`**

Set one or more custom boolean attribute key-value pairs, e.g. `receive_notifications=True`.
Allowed values are case insensitive variants of `1`, `true`, `t`, `yes` and `y`
Any other values will equate to `False`

**`-f, --float-attrs <key=value>`**

Set one or more custom boolean attribute key-value pairs, e.g. `score=7.8`.

**`-i, --int-attrs <key=value>`**

Set one or more custom integer attribute key-value pairs, e.g. `remaining_tokens=4`

**`-s, --str-attrs <key=value>`**

Set one or more custom string attribute key-value pairs, e.g. `name=Saturn`

---

## **create-role**

Create a new role in the database.

**`litestar users create-role [OPTIONS]`**

Options

**`--name <name>`**

The role name.

**`--description <description>`**

The role description.

---

## **assign-role**

Assign a role to a user.

### `litestar users assign-role [OPTIONS]`

Options

**`--email <email>`**

The user's email address.

**`--role <role>`**

The name of the role to assign.
