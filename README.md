# Crow Algo

A crypto spot-trading bot with configurable budgets, explainable decisions, and a web dashboard.

**Status:** specification only. Trading, GUI, and hosting are not implemented. No trades are placed.

## Direction

Start with one Kraken BTC/EUR momentum strategy on completed hourly candles in paper mode. Build the core so additional markets, strategy instances, and a live execution adapter can be added without replacing it.

Budgets, purchase sizes, position limits, and loss thresholds are configuration, not fixed amounts. Strategies have separate allocations; a shared risk manager prevents overspending.

Recommended GUI: React + TypeScript + Vite with a FastAPI backend, served together from one server. This recommendation is not yet an implemented or final dependency choice.

## Documentation

- [Product](doc/product.md): behavior and scope.
- [Architecture](doc/architecture.md): components, extensibility, and GUI recommendation.
- [Implementation](doc/implementation.md): ordered milestones and acceptance checks.
- [Agent instructions](AGENTS.md): contribution rules and documentation limits.

These five files are the complete documentation set. Update them instead of adding more.

## Development and operation

No installation or run command exists yet. Add verified setup, test, backup, and operating commands here as implementation lands.

Paper mode is the initial release. Future live operation requires an implemented, validated adapter and explicit activation. Credentials alone never enable live trading.
