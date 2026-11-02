# Crow Algo

A small crypto spot-trading bot designed for one market, one strategy, and a €50 total budget.

**Status:** specification only. The bot, dashboard, and deployment are not implemented yet. Nothing in this repository currently places trades.

## First version

- Kraken BTC/EUR, using completed hourly candles.
- One configurable momentum strategy.
- Paper trading with public market data, realistic fees, spread, and exchange minimums.
- A €50 total virtual budget; purchase size and risk limits are configurable.
- A dashboard for status, balances, positions, decisions, orders, trades, and logs.
- Continuous operation on a single cloud server with persistent SQLite storage.

Kraken, BTC/EUR, and momentum are initial defaults. Exact strategy parameters, purchase size, and loss limits must be agreed before implementation. A €50 budget is an allocation limit, not an instruction to spend €50 per trade.

## Project documents

- [Product](PRODUCT.md): behavior, scope, and delivery order.
- [Architecture](ARCHITECTURE.md): technical structure and correctness rules.
- [Agent instructions](AGENTS.md): contribution rules and documentation limits.

These four files are the complete documentation set. Keep them short and update them as the software changes.

## Development and operation

No installation or run command exists yet. Add verified setup, test, backup, and operating commands here when those features are implemented.

The initial release is paper-only. Live trading requires a separately requested exchange adapter and validation; it must never activate merely by supplying credentials.
