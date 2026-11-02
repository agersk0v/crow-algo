# Crow Algo

A crypto spot-trading bot with configurable budgets, explainable decisions, and a web dashboard.

**Status:** typed contracts, configuration validation, PostgreSQL configuration persistence/migrations, and a session-ownership primitive are implemented. Trading, API, GUI, and hosting are not implemented. No trades are placed.

The first release targets one Kraken BTC/EUR momentum strategy on hourly candles in paper mode. The design supports later additional markets, separate strategy allocations, and live execution. See [product](doc/product.md) for behavior and scope.

The planned stack is Next.js, Python/FastAPI, and PostgreSQL, started with Docker Compose. See [architecture](doc/architecture.md) for packages, data sources, and service design.

## Documentation

- [Product](doc/product.md): requirements, behavior, scope, and exclusions.
- [Architecture](doc/architecture.md): technical structure and decisions.
- [Implementation](doc/implementation.md): milestones, open decisions, acceptance checks, and progress.
- [Agent instructions](AGENTS.md): contribution and documentation maintenance rules.

## Development and operation

Use Python 3.12 and [uv](https://docs.astral.sh/uv/) 0.12.23. From the repository root:

```sh
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
```

The lockfile pins runtime and development dependencies. Unit tests need no database; integration tests skip unless `CROW_TEST_ADMIN_URL` is supplied. No tests use exchange credentials or market data. If the default cache is not writable, set `UV_CACHE_DIR=/tmp/crow-algo-uv-cache`.

For a database-free check, run `uv run --locked pytest -m 'not integration'`. For the full suite, supply `CROW_TEST_ADMIN_URL` pointing to a **disposable PostgreSQL 17 test server**, then run:

```sh
uv run --locked pytest --require-postgres
```

Use a test-only administrator able to create/drop databases and roles and terminate test sessions. Each integration test creates a randomly named database and migration/runtime roles; cleanup drops only those generated resources, never the supplied administrator database. Do not use production administrator credentials. CI runs the full suite against PostgreSQL 17.7.

### Database setup and migrations

Provision a database owned by a migration login and a separate runtime login with no administrative privileges. Example SQL for an administrator on a new local database server:

```sql
CREATE ROLE crow_migrate LOGIN;
CREATE ROLE crow_runtime LOGIN;
CREATE DATABASE crow_algo OWNER crow_migrate;
```

Set login passwords separately using protected credential tooling. Supply `CROW_MIGRATION_DATABASE_URL` for migration commands and `CROW_DATABASE_URL` for runtime code, both with the `postgresql+psycopg` driver. For example, a URL without embedded credentials is `postgresql+psycopg://crow_runtime@localhost:5432/crow_algo`; use protected libpq password files or injected secrets for authentication. The migration command does not fall back to runtime credentials.

From the repository root, initialize or upgrade with the migration-role URL configured:

```sh
uv run --locked alembic upgrade head
uv run --locked alembic current
```

After migration, the database owner grants runtime permissions on that database:

```sql
GRANT USAGE ON SCHEMA public TO crow_runtime;
GRANT SELECT, INSERT ON configuration_versions TO crow_runtime;
```

Do not grant runtime schema creation, table ownership, UPDATE, or DELETE. New databases should not grant PUBLIC schema-creation privileges. Migrations never reset existing records, and destructive downgrades are refused. CLI commands initialize schema only; they create no funding, positions, or orders.

`database_engine()` reads the runtime URL. Within `engine.begin()`, `save_configuration(connection, config)` appends a validated version and `load_configuration(connection, version)` reads it. Reusing a version is an error; the caller must roll back failed transactions. See [storage design](doc/architecture.md#storage-and-recovery) for scope and ownership semantics.

`crow_algo.config.Configuration.model_validate_json(text)` validates a JSON configuration; `model_dump_json()` serializes amounts as exact decimal strings. `validate_activation(config, [strategy_id])` separately checks initial-release eligibility. It never starts a process, funds an account, or places an order. See [architecture](doc/architecture.md#configuration-and-contracts) for the configuration structure and current restrictions.

No runnable services or Compose configuration exist yet. Verified service, backup, and restore commands will be added here as implementation lands. Planned delivery is tracked in [implementation](doc/implementation.md).

Paper mode is the initial release; live trading requires separate implementation, validation, and explicit activation.
