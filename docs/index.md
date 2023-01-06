# Starlite-Users documentation

Starlite-Users is an authentication, authorization and user management package for [Starlite](https://github.com/starlite-api/starlite) v1.43.0 and above.

## Features

* Supports Session, JWT and JWTCookie authentication backends
* Authorization via role based guards
* Pre-configured route handlers for:
  * Authentication
  * Registration
  * Verification
  * Password reset
  * Administrative user management (read, update, delete)
  * Administrative role management (read, update, delete)
  * Assignment/revocation of roles to/from users

## Installation

`pip install starlite-users`

## Full example

An example application can be viewed [here](https://github.com/LonelyVikingMichael/starlite-users/blob/main/examples/main.py).
