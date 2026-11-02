"""Read-only health endpoints; application lifecycle never starts trading."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import Engine, select, text
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from crow_algo.database import configuration_versions, database_engine


def create_app(
    engine: Engine | None = None, *, migration_config: Path = Path("alembic.ini")
) -> FastAPI:
    expected = ScriptDirectory.from_config(
        Config(str(migration_config))
    ).get_current_head()
    if expected is None:
        raise RuntimeError("migration head is not configured")
    database = engine

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        nonlocal database
        database = engine if engine is not None else database_engine()
        try:
            yield
        finally:
            if engine is None and database is not None:
                await run_in_threadpool(database.dispose)
            database = None

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health/live")
    async def live() -> dict[str, str | bool]:
        return {"status": "alive", "trading_enabled": False}

    @app.get("/health/ready")
    def ready() -> JSONResponse:
        # FastAPI runs synchronous handlers in its thread pool, not the event loop.
        try:
            if database is None:
                raise RuntimeError("application has not started")
            with database.connect() as connection:
                revisions = (
                    connection.execute(text("SELECT version_num FROM alembic_version"))
                    .scalars()
                    .all()
                )
                connection.execute(select(configuration_versions.c.version).limit(0))
            if revisions != [expected]:
                raise RuntimeError("schema mismatch")
        except (SQLAlchemyError, RuntimeError):
            return JSONResponse(
                {"status": "unavailable", "trading_enabled": False}, status_code=503
            )
        return JSONResponse({"status": "ready", "trading_enabled": False})

    return app
