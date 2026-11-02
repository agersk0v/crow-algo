"""Create only test-owned databases/roles; never migrate or drop the admin DB."""

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

from crow_algo.database import database_engine, database_url

ROOT = Path(__file__).resolve().parents[2]


def dsn(url: URL) -> str:
    return url.set(drivername="postgresql").render_as_string(hide_password=False)


@dataclass(repr=False)
class Database:
    migration_url: URL
    runtime_url: URL
    admin_url: URL

    def migrate(self) -> None:
        settings = Config(str(ROOT / "alembic.ini"))
        engine = database_engine(self.migration_url)
        try:
            with engine.begin() as connection:
                settings.attributes["connection"] = connection
                command.upgrade(settings, "head")
        finally:
            engine.dispose()

    def grant_runtime(self) -> None:
        with psycopg.connect(dsn(self.migration_url), connect_timeout=5) as connection:
            role = sql.Identifier(str(self.runtime_url.username))
            connection.execute(
                sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role)
            )
            connection.execute(
                sql.SQL("GRANT SELECT, INSERT ON configuration_versions TO {}").format(
                    role
                )
            )


@pytest.fixture
def database(request: pytest.FixtureRequest) -> Iterator[Database]:
    value = os.environ.get("CROW_TEST_ADMIN_URL")
    if not value:
        if request.config.getoption("--require-postgres"):
            pytest.fail("CROW_TEST_ADMIN_URL is required")
        pytest.skip("set CROW_TEST_ADMIN_URL to run PostgreSQL integration tests")
    admin_url = database_url(value)
    suffix = uuid4().hex
    name = "crow_test_" + suffix
    migration_role = "crow_migrate_" + suffix
    runtime_role = "crow_runtime_" + suffix
    # Generated credentials are used only for these disposable test roles.
    password = uuid4().hex
    with psycopg.connect(dsn(admin_url), autocommit=True, connect_timeout=5) as admin:
        created_roles: list[str] = []
        created_database = False
        try:
            for role in (migration_role, runtime_role):
                admin.execute(
                    sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                        sql.Identifier(role), sql.Literal(password)
                    )
                )
                created_roles.append(role)
            admin.execute(
                sql.SQL("CREATE DATABASE {} OWNER {} TEMPLATE template0").format(
                    sql.Identifier(name), sql.Identifier(migration_role)
                )
            )
            created_database = True
            yield Database(
                migration_url=admin_url.set(
                    database=name, username=migration_role, password=password
                ),
                runtime_url=admin_url.set(
                    database=name, username=runtime_role, password=password
                ),
                admin_url=admin_url.set(database=name),
            )
        finally:
            if created_database:
                admin.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                        sql.Identifier(name)
                    )
                )
            for role in reversed(created_roles):
                admin.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@pytest.fixture
def runtime(database: Database) -> Iterator[Engine]:
    database.migrate()
    database.grant_runtime()
    engine = database_engine(database.runtime_url)
    try:
        yield engine
    finally:
        engine.dispose()
