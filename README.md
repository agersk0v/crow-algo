# Crow Algo

A crypto spot-trading bot with configurable budgets, explainable decisions, and a web dashboard.

**Status:** configuration/contracts, PostgreSQL persistence, migrations, ownership primitive, a local health-only FastAPI backend, and offline momentum signal evaluation are implemented. Docker Compose starts the backend/database. Paper execution, GUI, authentication, and production hosting remain planned. No trades are placed.

The first release targets one Kraken BTC/EUR momentum strategy on hourly candles in paper mode. The design supports later additional markets, separate strategy allocations, and live execution. See [product](docs/product.md) for behavior and scope.

The planned stack is Next.js, Python/FastAPI, and PostgreSQL, started with Docker Compose. See [architecture](docs/architecture.md) for packages, data sources, and service design.

The repository follows the crow-fitness layout: `backend/` contains the Python package, tooling, migrations, Dockerfile, and tests; `scripts/smoke.sh` checks disposable Compose installations; `docs/` holds specifications. `frontend/` will be added with the GUI. See [repository layout](docs/architecture.md#repository-layout).

## Documentation

- [Product](docs/product.md): requirements, behavior, scope, and exclusions.
- [Architecture](docs/architecture.md): technical structure and decisions.
- [Implementation](docs/implementation.md): milestones, open decisions, acceptance checks, and progress.
- [Agent instructions](AGENTS.md): contribution and documentation maintenance rules.

## Development and operation

### Start locally with Docker Compose

Use Docker with Compose v2. From the repository root:

```sh
cp .env.example .env
chmod 600 .env
```

Set a unique `CROW_DB_PASSWORD` in `.env`, then start:

```sh
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 90
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
docker compose ps
docker compose logs -f --tail=100
```

There are two services: `db` and `backend`. One application login owns the database schema; minimal initialization creates that normal login and disables PostgreSQL's built-in administrator login. The backend applies versioned Alembic migrations before starting HTTP. No separate migration container, account grants, credential generator, or password files are needed. PostgreSQL has no published port; the API binds to localhost. Set `CROW_API_PORT` in `.env` to use another HTTP port.

`.env` is ignored by Git and excluded from image builds. Keep it private: the password is injected at runtime and is visible to Docker/environment administrators. Changing it does not change the password in an existing database volume. Earlier versions of this PR used separate logins; existing volumes require an explicit ownership/credential migration, not deletion or automatic reset.

Liveness returns 200 while HTTP responds. Readiness returns 200 only when database/schema access is usable, otherwise 503. Both report `trading_enabled: false`. No authentication or write/trading endpoints exist; this is a local development installation, not a public/live deployment.

```sh
docker compose restart backend
docker compose down
docker compose up -d --build --wait --wait-timeout 90
```

Normal shutdown/rebuild preserves the named PostgreSQL volume. **Do not use `down --volumes` on an installation you need to retain.** Backup/restore, production credentials, and separation of database administration follow in the hosting/live milestones.

### Development checks

Use Python 3.12 and [uv](https://docs.astral.sh/uv/) 0.12.23. From the repository root:

```sh
uv --directory backend sync --locked
uv --directory backend run --locked ruff check --config pyproject.toml .
uv --directory backend run --locked ruff format --config pyproject.toml --check .
uv --directory backend run --locked mypy
bash -n scripts/smoke.sh
uv --directory backend run --locked pytest
```

The lockfile pins runtime and development dependencies. Unit tests need no database; integration tests skip unless `CROW_TEST_ADMIN_URL` is supplied. No tests use exchange credentials or market data. If the default cache is not writable, set `UV_CACHE_DIR=/tmp/crow-algo-uv-cache`.

For a database-free check, run `uv --directory backend run --locked pytest -m 'not integration'`. For the full suite, supply `CROW_TEST_ADMIN_URL` pointing to a **disposable PostgreSQL 17 test server**, then run:

```sh
uv --directory backend run --locked pytest --require-postgres
```

Use a test-only administrator able to create/drop databases and roles and terminate test sessions. Each integration test creates a randomly named database and one schema-owner login; cleanup drops only those generated resources, never the supplied administrator database. Do not use production administrator credentials. CI runs the full suite against PostgreSQL 17.7.

CI also builds an isolated Compose project and verifies backend/database restart, database outage/recovery, and normal down/up persistence using `scripts/smoke.sh`. The script requires Bash, curl, and Docker Compose; database assertions use Python inside the backend container. It writes a synthetic zero-budget configuration and is restricted to explicitly named `crow-test-*` projects; do not run it against an installation with existing records.

### Database setup and migrations

Compose initializes the database automatically. Outside Compose, use a schema-owner login and set `CROW_DATABASE_URL` with the `postgresql+psycopg` driver. Keep passwords out of URLs and shell history; supply authentication through libpq's protected password file or `PGPASSWORD`. There is no separate migration URL.

From the repository root:

```sh
uv --directory backend run --locked python -m crow_algo.storage.migrate
uv --directory backend run --locked alembic current
```

Migrations are transactional and serialized, preserve existing records, and refuse destructive downgrades. The application account can change its schema; restricted migration/runtime accounts are deferred until operational needs justify them. Schema initialization creates no funding, positions, or orders.

`database_engine()` reads the runtime URL. Within `engine.begin()`, `save_configuration(connection, config)` appends a validated version and `load_configuration(connection, version)` reads it. Reusing a version is an error; the caller must roll back failed transactions. See [storage design](docs/architecture.md#storage-and-recovery) for scope and ownership semantics.

`crow_algo.config.Configuration.model_validate_json(text)` validates a JSON configuration; `model_dump_json()` serializes amounts as exact decimal strings. `validate_activation(config, [strategy_id])` separately checks initial-release eligibility. It never starts a process, funds an account, or places an order. See [architecture](docs/architecture.md#configuration-and-contracts) for the configuration structure and current restrictions.

### Evaluate the offline strategy

`crow_algo.strategies.momentum.MomentumStrategy().evaluate(market, candles, parameters, as_of=timestamp)` accepts a `Market`, a tuple of validated `Candle` records, a parameter dictionary, and an explicit timezone-aware evaluation time. For example, `parameters={"lookback": 24, "entry_threshold_pct": "2", "exit_threshold_pct": "-1"}` uses the initial defaults. It returns a `Signal` with intent and reason; it does not fetch prices, persist decisions, or place orders. See [strategy rules](docs/product.md#momentum-v1-rules) for behavior and history requirements.

Run the synthetic strategy examples and edge cases without a database:

```sh
uv --directory backend run --locked pytest tests/test_momentum.py
```

Planned delivery is tracked in [implementation](docs/implementation.md).

Paper mode is the initial release; live trading requires separate implementation, validation, and explicit activation.
