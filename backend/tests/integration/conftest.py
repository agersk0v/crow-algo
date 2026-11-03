"""Create test-owned databases and one owner login; never alter the admin DB."""

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy import Engine
from sqlalchemy.engine import URL

from crow_algo.storage.database import database_engine, database_url

ROOT = Path(__file__).resolve().parents[2]


def dsn(url: URL) -> str:
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


@dataclass(repr=False)
class Database:
    app_url: URL
    admin_url: URL

    def migrate(self) -> None:
        settings = Config(str(ROOT / "alembic.ini"))
        engine = database_engine(self.app_url)
        try:
            with engine.begin() as connection:
                settings.attributes["connection"] = connection
                command.upgrade(settings, "head")
        finally:
            engine.dispose()


@pytest.fixture
def database(request: pytest.FixtureRequest) -> Iterator[Database]:
    value = os.environ.get("CROW_TEST_ADMIN_URL")
    if not value:
        if request.config.getoption("--require-postgres"):
            pytest.fail("CROW_TEST_ADMIN_URL is required")
        pytest.skip("set CROW_TEST_ADMIN_URL to run PostgreSQL integration tests")
    admin_url = database_url(value)
    suffix = uuid4().hex
    name, role = "crow_test_" + suffix, "crow_app_" + suffix
    password = uuid4().hex
    with psycopg.connect(dsn(admin_url), autocommit=True, connect_timeout=5) as admin:
        created_role = created_database = False
        try:
            admin.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(role), sql.Literal(password)
                )
            )
            created_role = True
            admin.execute(
                sql.SQL("CREATE DATABASE {} OWNER {} TEMPLATE template0").format(
                    sql.Identifier(name), sql.Identifier(role)
                )
            )
            created_database = True
            yield Database(
                app_url=admin_url.set(database=name, username=role, password=password),
                admin_url=admin_url.set(database=name),
            )
        finally:
            if created_database:
                admin.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                        sql.Identifier(name)
                    )
                )
            if created_role:
                admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@pytest.fixture
def runtime(database: Database) -> Iterator[Engine]:
    database.migrate()
    engine = database_engine(database.app_url)
    try:
        yield engine
    finally:
        engine.dispose()
