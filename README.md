# starlite-users
Authentication, authorization and user management for the Starlite framework

_This package is not yet production ready._
---
## Features
* Supports Starlite Session, JWT and JWTCookie auth backends
* SQLAlchemy ORM models (Piccolo and Tortoise on roadmap)
* Pre-configured route handlers for:
  * Authentication
  * Registration
  * Verification
  * Password reset
  * Administrative user management
* Authorization via role based guards
* Define your own administrative roles for user management

## Getting started
The package is not yet availabe on PyPi. Right now you can:
1. Clone this repository
2. `cd starlite-users && poetry install`
3. `poetry run PYTHONPATH=. python examples/main.py`

This will start a `uvicorn` server running on `127.0.0.1:8000`
Visit `127.0.0.1:8000/schema/swagger` for interactive docs
