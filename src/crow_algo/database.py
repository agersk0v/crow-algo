"""Bounded PostgreSQL access and append-only configuration persistence."""

import os
from pathlib import Path
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    Engine,
    MetaData,
    Table,
    create_engine,
    func,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import URL, Connection, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from crow_algo.config import Configuration

metadata = MetaData()
configuration_versions = Table(
    "configuration_versions",
    metadata,
    Column("version", BigInteger, primary_key=True, autoincrement=False),
    Column("document", JSONB, nullable=False),
    Column(
        "created_at", DateTime(timezone=True), nullable=False, server_default=func.now()
    ),
    CheckConstraint("version > 0", name="positive_configuration_version"),
    CheckConstraint(
        "jsonb_typeof(document) = 'object' "
        "AND document ? 'version' "
        "AND document->'version' = to_jsonb(version) "
        "AND document @> '{\"schema_version\": 1}'::jsonb",
        name="matching_configuration_document",
    ),
)


class PersistenceError(RuntimeError):
    """Safe diagnostic without credentials, SQL parameters, or stored payloads."""


def database_url(value: str | URL | None = None, *, migration: bool = False) -> URL:
    password_file: str | None = None
    if value is None:
        variable = "CROW_MIGRATION_DATABASE_URL" if migration else "CROW_DATABASE_URL"
        value = os.environ.get(variable)
        password_file = os.environ.get(variable.removesuffix("_URL") + "_PASSWORD_FILE")
    if not value:
        raise PersistenceError("database connection is not configured")
    try:
        url = make_url(value)
    except Exception:
        raise PersistenceError("invalid database connection configuration") from None
    if url.drivername != "postgresql+psycopg":
        raise PersistenceError("database URL must use postgresql+psycopg")
    if password_file:
        if url.password is not None:
            raise PersistenceError(
                "configure a password file or URL password, not both"
            )
        try:
            password = Path(password_file).read_text().rstrip("\r\n")
        except (OSError, UnicodeError):
            raise PersistenceError("database password file is unreadable") from None
        if not password:
            raise PersistenceError("database password file is empty")
        url = url.set(password=password)
    return url


def database_engine(
    value: str | URL | None = None, *, dedicated: bool = False
) -> Engine:
    pool_options: dict[str, Any] = (
        {"poolclass": NullPool}
        if dedicated
        else {
            "pool_size": 2,
            "max_overflow": 0,
            "pool_timeout": 5,
            "pool_pre_ping": True,
        }
    )
    return create_engine(
        database_url(value),
        hide_parameters=True,
        connect_args={
            "connect_timeout": 5,
            "keepalives_idle": 5,
            "keepalives_interval": 1,
            "keepalives_count": 3,
            "tcp_user_timeout": 5000,
            "options": "-c statement_timeout=5000 -c lock_timeout=2000 "
            "-c idle_in_transaction_session_timeout=15000 -c timezone=UTC",
        },
        **pool_options,
    )


def save_configuration(connection: Connection, config: Configuration) -> None:
    """Append within the caller's transaction; never commit or overwrite."""
    # Revalidate nested mutable parameter dictionaries before persisting.
    validated = Configuration.model_validate(config.model_dump(mode="python"))
    try:
        connection.execute(
            insert(configuration_versions).values(
                version=validated.version,
                document=validated.model_dump(mode="json"),
            )
        )
    except SQLAlchemyError:
        raise PersistenceError(
            "configuration insert failed; transaction must roll back"
        ) from None


def load_configuration(connection: Connection, version: int) -> Configuration:
    try:
        document: Any = connection.execute(
            select(configuration_versions.c.document).where(
                configuration_versions.c.version == version
            )
        ).scalar_one_or_none()
    except SQLAlchemyError:
        raise PersistenceError("configuration read failed") from None
    if document is None:
        raise PersistenceError("configuration version not found")
    return Configuration.model_validate(document)
