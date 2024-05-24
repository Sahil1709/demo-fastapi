# FastAPI Demo Project

## Dependencies
- [FastAPI](https://fastapi.tiangolo.com/): A modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.
- [Pytest](https://pytest.org/): A mature full-featured Python testing tool that helps you write better programs.
- [Alembic](https://alembic.sqlalchemy.org/): A lightweight database migration tool for usage with SQLAlchemy.
- [Bcrypt](https://pypi.org/project/bcrypt/): A password hashing function designed by Niels Provos and David Mazières, based on the Blowfish cipher.
- [Apscheduler](https://apscheduler.readthedocs.io/): A Python library that lets you schedule your Python code to be executed later, either just once or periodically.

## Prerequisites

- [Poetry](https://python-poetry.org/) should be installed on your system.

## Setup

1. Create a `.env` file in the root directory of the project.
2. Add the `POSTGRES_DB_URL` environment variable to the `.env` file. This should contain the connection URL for your PostgreSQL database.

## Installation

Run the following commands to install the project dependencies and start fastapi server on development mode.

```sh
poetry install
poetry run fastapi dev app/main.py
```