"""Use an explicitly supplied migration connection or application URL."""

from alembic import context
from sqlalchemy.engine import Connection

from crow_algo.database import database_engine, metadata


def run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=metadata)
    with context.begin_transaction():
        context.run_migrations()


provided = context.config.attributes.get("connection")
if provided is not None:
    run(provided)
elif context.is_offline_mode():
    raise RuntimeError("offline migrations are not supported")
else:
    engine = database_engine()
    try:
        with engine.connect() as connection:
            run(connection)
    finally:
        engine.dispose()
