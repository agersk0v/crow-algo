# Product

## Goal

Run a small, understandable crypto bot continuously and make its activity visible. Start with one market, one strategy, and €50 total. Reliable behavior and explainable decisions matter more than feature count. No profitability is promised.

## Initial scope

- One exchange and spot pair: initially Kraken BTC/EUR.
- One momentum strategy using completed one-hour candles.
- Long-only: buy with available EUR, hold BTC, and sell owned BTC.
- Paper trading using timestamped public quotes after the decision: buy at ask, sell at bid, apply explicit fees and configured slippage.
- Respect market quantity precision and minimum order amounts. Skip unaffordable orders with an explanation.
- One €50 virtual account and at most one BTC position. No additional purchases while a position or entry order exists.
- Configurable purchase amount, position cap, total budget, loss limit, and strategy parameters.
- Strategy modules share a small interface so another strategy can be added later; only one is active initially.

## Visibility and controls

The dashboard shows mode, running/paused/error status, last successful update, quote freshness, cash, holdings, equity history, fees, and realized/unrealized profit or loss. It lists decisions and their reasons, order status, fills, and searchable timestamped operational logs.

Pause prevents new purchases while monitoring and exits continue. Stopping the process pauses all processing and does not sell holdings. Neither action silently liquidates positions.

Configuration changes are validated and recorded with effective times. Initially, changes to strategy, candle interval, or execution mode require a paused bot with no position or pending order. Budget changes must be explicit and recorded; restart never resets balances.

## Reliability

- Run on one cloud server with automatic process restart and persistent storage.
- Recover after restart without duplicate funding, decisions, or orders.
- Refuse new entries when prices are stale, data is incomplete, or accounting cannot be reconciled.
- Keep trade records and backups. Never silently replace missing prices or invent successful fills.
- Protect dashboard access before exposing it on the internet.

## Later live trading

Keep execution separate from strategy and risk logic. A live adapter needs explicit activation, restricted exchange credentials, exchange-side reconciliation, partial-fill handling, and recovery from ambiguous order submissions. Live trading is not part of the first release.

## Excluded initially

Stocks, FX conversion, multiple markets or simultaneous strategies, leverage, shorting, derivatives, deposits/withdrawals, a visual strategy builder, distributed workers, and a research/backtesting platform.

## Delivery order and acceptance

1. Build a deterministic offline buy/hold/sell example with fees, budget checks, restart recovery, and duplicate prevention.
2. Run hourly paper trading against public data, including outage and stale-data handling.
3. Add the dashboard, configuration controls, durable operational logs, and equity history.
4. Deploy one authenticated instance with automatic restart, backup, and a verified restore.

Before implementation, settle momentum entry/exit lookbacks, purchase amount, position cap, loss threshold and its action, fee/slippage assumptions, and hosting. A configuration example must not invent these as approved trading settings.
