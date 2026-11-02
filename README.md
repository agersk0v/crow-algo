# Crow Algo

A crypto spot-trading bot with configurable budgets, explainable decisions, and a web dashboard.

**Status:** specification only. Trading, GUI, and hosting are not implemented. No trades are placed.

## Direction

Start with one Kraken BTC/EUR momentum strategy on completed hourly candles in paper mode. Build the core so additional markets, strategy instances, and a live execution adapter can be added without replacing it.

Budgets, purchase sizes, position limits, and loss thresholds are configuration, not fixed amounts. Strategies have separate allocations; a shared risk manager prevents overspending.

Frontend: Next.js + TypeScript, Tailwind CSS, shadcn/ui, and TradingView Lightweight Charts. Backend: FastAPI and the Python trading engine. Docker Compose starts both services on one server.

## Documentation

- [Product](doc/product.md): behavior and scope.
- [Architecture](doc/architecture.md): components, extensibility, and GUI design.
- [Implementation](doc/implementation.md): ordered milestones and acceptance checks.
- [Agent instructions](AGENTS.md): contribution rules and documentation limits.

These five files are the complete documentation set. Update them instead of adding more.

## Development and operation

Docker Compose is the chosen startup workflow. Once the services and Compose configuration are implemented, the intended commands are:

```sh
docker compose up -d --build
docker compose ps
docker compose logs -f --tail=100
docker compose down
```

These commands are planned, not runnable in this specification-only repository yet. Backend data will live in a named volume and survive container recreation and normal shutdown. Never use `docker compose down -v` on an active installation: it deletes named volumes.

Add verified setup, configuration, test, backup, and restore instructions here as implementation lands. Docker log following complements the dashboard's durable, searchable activity history.

Paper mode is the initial release. Future live operation requires an implemented, validated adapter and explicit activation. Credentials alone never enable live trading.
