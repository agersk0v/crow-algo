# Crow Algo

A crypto spot-trading bot with configurable budgets, explainable decisions, and a web dashboard.

**Status:** Python package, typed contracts, and configuration validation implemented. Trading, database persistence, API, GUI, and hosting are not implemented. No trades are placed.

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

The lockfile pins runtime and development dependencies. Tests need no database, market data, or credentials. If the default cache is not writable, set `UV_CACHE_DIR=/tmp/crow-algo-uv-cache`.

`crow_algo.config.Configuration.model_validate_json(text)` validates a JSON configuration; `model_dump_json()` serializes amounts as exact decimal strings. `validate_activation(config, [strategy_id])` separately checks initial-release eligibility. It never starts a process, funds an account, or places an order. See [architecture](doc/architecture.md#configuration-and-contracts) for the configuration structure and current restrictions.

No runnable services or Compose configuration exist yet. Verified service, backup, and restore commands will be added here as implementation lands. Planned delivery is tracked in [implementation](doc/implementation.md).

Paper mode is the initial release; live trading requires separate implementation, validation, and explicit activation.
