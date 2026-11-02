# Crow Algo

A crypto spot-trading bot with configurable budgets, explainable decisions, and a web dashboard.

**Status:** specification only. Trading, GUI, and hosting are not implemented. No trades are placed.

The first release targets one Kraken BTC/EUR momentum strategy on hourly candles in paper mode. The design supports later additional markets, separate strategy allocations, and live execution. See [product](doc/product.md) for behavior and scope.

The planned stack is Next.js, Python/FastAPI, and PostgreSQL, started with Docker Compose. See [architecture](doc/architecture.md) for packages, data sources, and service design.

## Documentation

- [Product](doc/product.md): requirements, behavior, scope, and exclusions.
- [Architecture](doc/architecture.md): technical structure and decisions.
- [Implementation](doc/implementation.md): milestones, open decisions, acceptance checks, and progress.
- [Agent instructions](AGENTS.md): contribution and documentation maintenance rules.

## Development and operation

No runnable services or Compose configuration exist yet. Setup, run, test, backup, and restore commands will be added here as they are implemented and verified. Planned delivery is tracked in [implementation](doc/implementation.md).

Paper mode is the initial release; live trading requires separate implementation, validation, and explicit activation.
