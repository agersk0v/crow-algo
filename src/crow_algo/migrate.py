"""One-shot schema upgrade and runtime grants, using migration credentials only."""

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.util.exc import CommandError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from crow_algo.database import PersistenceError, database_engine, database_url

# A migration lock is independent of the future trading-owner lock.
MIGRATION_LOCK = 0x43524F575F4D4947


def upgrade_database(
    *, migration_config: Path = Path("alembic.ini"), runtime_role: str = "crow_runtime"
) -> None:
    engine = database_engine(database_url(migration=True))
    try:
        with engine.begin() as connection:
            if not connection.execute(
                text("SELECT pg_try_advisory_xact_lock(:key)"), {"key": MIGRATION_LOCK}
            ).scalar_one():
                raise PersistenceError("another migration is in progress")
            config = Config(str(migration_config))
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
            role = connection.dialect.identifier_preparer.quote_identifier(runtime_role)
            connection.execute(text(f"GRANT USAGE ON SCHEMA public TO {role}"))
            connection.execute(
                text(f"GRANT SELECT, INSERT ON configuration_versions TO {role}")
            )
            connection.execute(text(f"GRANT SELECT ON alembic_version TO {role}"))
    finally:
        engine.dispose()


def main() -> int:
    try:
        upgrade_database()
    except (PersistenceError, SQLAlchemyError, CommandError, OSError):
        print(
            "Database initialization failed; existing records were not reset.",
            file=sys.stderr,
        )
        return 1
    print("Database initialized; trading is not enabled.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
