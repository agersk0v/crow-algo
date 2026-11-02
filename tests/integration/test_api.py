"""Readiness checks real schema state without funding accounts or taking locks."""

import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from crow_algo.api import create_app
from crow_algo.database import PersistenceError, database_engine
from crow_algo.migrate import MIGRATION_LOCK, upgrade_database

from .conftest import Database, dsn

pytestmark = pytest.mark.integration


def test_readiness_tracks_migration_state_without_writes_or_ownership(
    database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "CROW_MIGRATION_DATABASE_URL",
        database.migration_url.render_as_string(hide_password=False),
    )
    engine = database_engine(database.runtime_url)
    try:
        with TestClient(create_app(engine)) as client:
            assert client.get("/health/live").status_code == 200
            assert client.get("/health/ready").status_code == 503
            for _ in range(2):
                upgrade_database(runtime_role=str(database.runtime_url.username))
            assert client.get("/health/ready").json() == {
                "status": "ready",
                "trading_enabled": False,
            }
            with psycopg.connect(dsn(database.migration_url)) as connection:
                connection.execute("UPDATE alembic_version SET version_num='future'")
            assert client.get("/health/ready").status_code == 503
            with psycopg.connect(dsn(database.migration_url)) as connection:
                connection.execute("UPDATE alembic_version SET version_num='0001'")
            assert client.get("/health/ready").status_code == 200
        with engine.connect() as connection:
            assert (
                connection.execute(
                    text("SELECT count(*) FROM configuration_versions")
                ).scalar_one()
                == 0
            )
            assert (
                connection.execute(
                    text(
                        "SELECT count(*) FROM pg_locks "
                        "WHERE locktype='advisory' AND database="
                        "(SELECT oid FROM pg_database WHERE datname=current_database())"
                    )
                ).scalar_one()
                == 0
            )
    finally:
        engine.dispose()


def test_migration_and_grants_roll_back_together(
    database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "CROW_MIGRATION_DATABASE_URL",
        database.migration_url.render_as_string(hide_password=False),
    )
    with pytest.raises(DBAPIError):
        upgrade_database(runtime_role="missing_role")
    with psycopg.connect(dsn(database.migration_url)) as connection:
        assert connection.execute(
            "SELECT to_regclass('configuration_versions')"
        ).fetchone() == (None,)
        assert connection.execute(
            "SELECT to_regclass('alembic_version')"
        ).fetchone() == (None,)


def test_concurrent_migration_is_rejected(
    database: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "CROW_MIGRATION_DATABASE_URL",
        database.migration_url.render_as_string(hide_password=False),
    )
    with psycopg.connect(dsn(database.migration_url)) as owner:
        owner.execute("SELECT pg_advisory_xact_lock(%s)", (MIGRATION_LOCK,))
        with pytest.raises(PersistenceError, match="another migration"):
            upgrade_database(runtime_role=str(database.runtime_url.username))
