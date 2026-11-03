"""Real PostgreSQL migration, persistence, permissions, and session-lock tests."""

import os
import subprocess
import sys
from decimal import Decimal
from typing import Any

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy import Engine, insert, text
from sqlalchemy.exc import DBAPIError

from crow_algo.config import Configuration
from crow_algo.database import (
    PersistenceError,
    configuration_versions,
    database_engine,
    load_configuration,
    save_configuration,
)
from crow_algo.ownership import LOCK_KEY, OwnerLock, OwnershipLost, OwnershipUnavailable

from .conftest import ROOT, Database, dsn

pytestmark = pytest.mark.integration


def sample(version: int = 1) -> Configuration:
    return Configuration.model_validate(
        {
            "version": version,
            "markets": [
                {"id": "btc", "exchange": "kraken", "base": "BTC", "quote": "EUR"}
            ],
            "execution_accounts": [
                {
                    "id": "paper",
                    "exchange": "kraken",
                    "mode": "paper",
                    "quote_currency": "EUR",
                    "budget": "123.12345678901234567890123456789",
                }
            ],
            "allocation_accounts": [
                {
                    "id": "one",
                    "execution_account_id": "paper",
                    "budget": "12.345678901234567890123456789",
                }
            ],
            "strategies": [
                {
                    "id": "momentum",
                    "strategy_type": "momentum",
                    "strategy_version": 1,
                    "market_ids": ["btc"],
                    "timeframe": "1h",
                    "allocation_account_id": "one",
                    "parameters": {"nested": [1, True, "example"]},
                }
            ],
        }
    )


def test_roundtrip_and_repeated_migration_preserve_exact_records(
    database: Database, runtime: Engine
) -> None:
    original = sample()
    with runtime.begin() as connection:
        save_configuration(connection, original)
    database.migrate()
    with runtime.connect() as connection:
        restored = load_configuration(connection, 1)
        created_at = connection.execute(
            text("SELECT created_at FROM configuration_versions")
        ).scalar_one()
    assert restored == original
    assert restored.execution_accounts[0].budget == Decimal(
        "123.12345678901234567890123456789"
    )
    assert created_at.tzinfo is not None
    # Reopen a fresh pool, as a new process would, without resetting state.
    reopened = database_engine(database.app_url)
    try:
        with reopened.connect() as connection:
            assert load_configuration(connection, 1) == original
    finally:
        reopened.dispose()


def test_append_only_and_transaction_rollback(runtime: Engine) -> None:
    with runtime.begin() as connection:
        save_configuration(connection, sample())
    with pytest.raises(PersistenceError, match="insert failed"):
        with runtime.begin() as connection:
            save_configuration(connection, sample(2))
            save_configuration(connection, sample())
    with runtime.connect() as connection:
        assert load_configuration(connection, 1) == sample()
        with pytest.raises(PersistenceError, match="not found"):
            load_configuration(connection, 2)


def test_mutated_configuration_is_revalidated_before_write(runtime: Engine) -> None:
    config = sample()
    config.strategies[0].parameters["threshold"] = float("nan")
    with pytest.raises(ValidationError):
        with runtime.begin() as connection:
            save_configuration(connection, config)
    with runtime.connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM configuration_versions")
            ).scalar_one()
            == 0
        )


def test_cli_migration_uses_application_credentials(database: Database) -> None:
    environment = os.environ.copy()
    environment["CROW_DATABASE_URL"] = database.app_url.render_as_string(
        hide_password=False
    )
    for operation in ("upgrade", "upgrade", "current"):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", operation]
            + (["head"] if operation == "upgrade" else []),
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert result.returncode == 0, "migration CLI failed"
    engine = database_engine(database.app_url)
    try:
        with engine.begin() as connection:
            save_configuration(connection, sample())
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("version", "document"),
    [
        (0, {"version": 0, "schema_version": 1}),
        (1, {"version": 2, "schema_version": 1}),
        (1, {"schema_version": 1}),
        (1, {"version": 1}),
        (1, {"version": 1, "schema_version": 2}),
        (1, []),
    ],
)
def test_database_checks_reject_invalid_snapshots(
    runtime: Engine, version: int, document: Any
) -> None:
    with pytest.raises(DBAPIError):
        with runtime.begin() as connection:
            connection.execute(
                insert(configuration_versions).values(
                    version=version, document=document
                )
            )


def test_failed_migration_does_not_remove_existing_tables(database: Database) -> None:
    with psycopg.connect(dsn(database.app_url), connect_timeout=5) as connection:
        connection.execute("CREATE TABLE configuration_versions (sentinel text)")
        connection.execute("INSERT INTO configuration_versions VALUES ('keep')")
    with pytest.raises(DBAPIError):
        database.migrate()
    with psycopg.connect(dsn(database.app_url), connect_timeout=5) as connection:
        assert connection.execute(
            "SELECT * FROM configuration_versions"
        ).fetchone() == ("keep",)
        assert connection.execute(
            "SELECT to_regclass('alembic_version')"
        ).fetchone() == (None,)


def test_application_owns_schema_without_cluster_administration(
    runtime: Engine,
) -> None:
    with runtime.begin() as connection:
        privileges = connection.execute(
            text(
                "SELECT rolsuper, rolcreatedb, rolcreaterole, "
                "rolreplication, rolbypassrls "
                "FROM pg_roles WHERE rolname=current_user"
            )
        ).one()
        assert privileges == (False, False, False, False, False)
        connection.execute(text("CREATE TABLE schema_change_check (id integer)"))
        connection.execute(text("DROP TABLE schema_change_check"))


def test_destructive_downgrade_is_refused(database: Database, runtime: Engine) -> None:
    with runtime.begin() as connection:
        save_configuration(connection, sample())
    settings = Config(str(ROOT / "alembic.ini"))
    engine = database_engine(database.app_url)
    try:
        with engine.begin() as connection:
            settings.attributes["connection"] = connection
            with pytest.raises(RuntimeError, match="destructive downgrade"):
                command.downgrade(settings, "base")
    finally:
        engine.dispose()
    with runtime.connect() as connection:
        assert load_configuration(connection, 1) == sample()


def test_single_owner_release_and_unpooled_session(database: Database) -> None:
    with OwnerLock(database.app_url) as first:
        first.check()
        with pytest.raises(OwnershipUnavailable, match="another session"):
            with OwnerLock(database.app_url):
                pytest.fail("duplicate owner was allowed")
        first.check()
    with pytest.raises(OwnershipLost):
        first.check()
    with OwnerLock(database.app_url) as replacement:
        replacement.check()


def test_terminated_session_loses_ownership_permanently(database: Database) -> None:
    with OwnerLock(database.app_url) as owner:
        owner.check()
        with psycopg.connect(
            dsn(database.admin_url), autocommit=True, connect_timeout=5
        ) as admin:
            row = admin.execute(
                "SELECT pid FROM pg_locks WHERE locktype='advisory' "
                "AND database=(SELECT oid FROM pg_database "
                "WHERE datname=current_database()) "
                "AND classid=%s AND objid=%s AND objsubid=1 AND granted",
                (LOCK_KEY >> 32, LOCK_KEY & 0xFFFFFFFF),
            ).fetchone()
            assert row is not None
            assert admin.execute(
                "SELECT pg_terminate_backend(%s)", (row[0],)
            ).fetchone() == (True,)
        with pytest.raises(OwnershipLost):
            owner.check()
        with OwnerLock(database.app_url) as replacement:
            replacement.check()
            with pytest.raises(OwnershipLost):
                owner.check()
