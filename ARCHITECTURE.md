# Architecture

## Approach

Use one Python application, one SQLite database, and one small web dashboard on a single server. Keep modules clear without introducing services, queues, or a plugin framework. This is a planned architecture; no runtime exists yet.

Flow: market data → strategy → risk checks → execution → persisted results → dashboard.

## Responsibilities

- **Market data:** fetch closed candles and timestamped bid/ask quotes through CCXT; validate freshness, ordering, gaps, prices, and exchange market rules. Candle interval is explicit rather than hardcoded to daily.
- **Strategy:** a pure function of validated closed candles and parameters, returning buy, sell, or hold with a reason. No networking, database writes, order sizing, or exchange credentials.
- **Risk:** check available budget, fees, position cap, market minimums, pause state, and configured loss limits. A strategy cannot bypass these checks.
- **Execution:** a small interface for submitting orders and reconciling status. Implement paper execution first; a future live adapter must represent pending, partial, filled, cancelled, rejected, and unknown outcomes.
- **Runner:** one sequential loop refreshes data, evaluates each newly closed candle once, monitors risk, and reconciles orders. Quote/risk checks may run more often than strategy evaluation. Retry temporary failures with bounded backoff.
- **Storage:** transactions for decisions, orders, fills, balances, and configuration history; unique identifiers prevent replay after restart.
- **Dashboard:** authenticated API and UI for state, history, logs, and validated controls. Commands are serialized through the trading loop so UI requests cannot race with execution.

## Persistence

Store candles, decisions, orders, fills, account/position state, equity samples, configuration versions, and control requests in one SQLite database. Use explicit money/quantity fields and indexes; use JSON only for supporting details where useful.

Use Decimal for accounting and exchange precision. Store timestamps in UTC and display the user's local timezone in the dashboard. Keep the decision inputs and quote evidence needed to explain each trade without a separate snapshot archive system.

Keep operational logs structured, timestamped, searchable, persistent across restarts, and rotated. Store financial history independently of log rotation. Secrets must never appear in either.

## Correctness and recovery

- Only evaluate completed candles; do not execute using a price observed before the order decision.
- Paper buys use ask and sells use bid; do not charge the spread twice. Full paper fills are an approximation, not evidence of live liquidity.
- Keep network calls outside database write transactions.
- Commit local financial changes atomically and reconcile balances, positions, orders, and fills before resuming trading.
- Never retry an ambiguous live submission blindly: persist intent first, use a stable client order ID where supported, and query exchange state.
- Never reset accounts, silently rewrite trade history, or infer a fill from a timeout.
- Enforce one trading-loop owner. Dashboard reads must not acquire financial write locks unnecessarily.

## Hosting and verification

Use a process supervisor or container restart policy, persistent local disk, HTTPS, authenticated dashboard access, and automatic SQLite-consistent backups. Verify restore in isolation. A development chat session is not production hosting.

Pin dependencies. Test strategy rules, closed-candle timing, fees/rounding, budget rejection, stale data, pause behavior, transaction rollback, restart deduplication, and complete buy/sell accounting. Live execution requires additional adapter and exchange-recovery tests.

Reuse small proven functions and safety tests from crow-trading where appropriate. Do not copy its daily scanner/database handoff, stock/FX machinery, or research archive architecture.
