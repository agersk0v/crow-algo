# Architecture

## Shape

One Python trading application, one SQLite database, and a web dashboard on one server. Keep strategy, market data, risk, execution, persistence, and presentation separate. Avoid distributed services and a general plugin framework.

Flow: market data → strategy signal → allocation/risk checks → order intent → execution/reconciliation → persisted state → dashboard.

This is a planned architecture; nothing is implemented yet.

## Identities and interfaces

- **Market:** exchange + market type + pair. Candle cache keys include market and interval; reuse data across strategies.
- **Strategy instance:** stable ID, strategy type/version, parameters, timeframe, selected markets, allocation account, and execution account/mode. One allocation can cover several markets.
- **Strategy interface:** pure evaluation of validated closed candles, returning enter/exit/hold and a reason. Strategies never submit orders, size positions, access secrets, or write storage.
- **Execution interface:** submit intent, query/reconcile order, and cancel. Paper first; live later. Preserve client intent IDs, exchange order IDs, fills, and explicit lifecycle states.
- **Risk:** enforce instance allocation, position limits, shared exposure, reservations, fees, precision, and exchange minimums. Use a common quote currency initially.

## Runtime and allocation

Use one trading-loop owner to serialize financial state changes and control commands. Deduplicate decisions by strategy instance, market, candle, and configuration version. Fetch each required candle series once; use bounded rate-limited provider calls. Do not implement concurrent worker infrastructure initially.

Maintain separate strategy ledgers and ownership of quantities. A shared risk layer prevents double allocation/spending across instances. Quote polling and order reconciliation can run more frequently than closed-candle strategy evaluation.

Keep network calls outside SQLite write transactions. Persist intent before external submission and reconcile after it. An unknown live outcome blocks conflicting action until resolved; never blindly resubmit. Support pending, partial, filled, cancelled, rejected, and unknown outcomes when implementing live execution.

## Storage and recovery

Use SQLite with explicit schema migrations, indexes, short transactions, and one financial writer. Persist execution/strategy accounts, allocations, configuration versions, candles, decisions, orders, fills, positions, financial events, equity samples, control commands, and heartbeat.

Use Decimal for accounting/precision and UTC timestamps. Store the signal inputs and quote evidence needed to explain each trade without a separate research snapshot system. Separate paper and live accounting; simulated capital never counts as exchange funds.

Commit local financial changes atomically. Reconcile cash, reservations, fills, and owned quantities on restart. Live adapters additionally reconcile exchange orders and balances, including partial fills and external/manual activity. Preserve records; do not reset accounts to recover.

Persist structured operational logs with severity, timestamp, market, strategy instance, and order IDs where relevant. Rotate operational logs independently of financial records. Retain periodic equity samples for charts, including unchanged periods. Never expose secrets.

## Recommended GUI

Use React + TypeScript + Vite for the frontend and FastAPI for the backend. Tailwind CSS and shadcn/ui are suitable styling/component choices; TradingView Lightweight Charts is suitable for candles and trade markers. Pin versions when implementation starts. Stack selection is a recommendation pending agreement.

Build a responsive dashboard: overview, positions/orders/trades, strategy configuration, and logs. Add market/strategy/mode filters as multiple instances arrive. Show stale data and paper/live mode prominently.

Serve the built frontend and API from one origin on one server; no separate frontend hosting or Next.js server is required. Use short polling initially; add server-sent events for logs/status only if needed. Keep trading independent of browser sessions and UI requests.

The backend validates configuration and records commands for the trading loop; the browser never accesses SQLite or exchange credentials directly. Authenticate access, protect write requests against CSRF when using cookies, and avoid unsafe rendering of log/provider text.

A server-rendered FastAPI + HTMX UI would reduce frontend tooling, but React better fits the intended configurable charts, tables, and future multi-strategy views. Streamlit is appropriate for a prototype, not the preferred operational control panel.

## Hosting and verification

Use persistent disk, HTTPS, process supervision, restricted secrets, SQLite-consistent backups, and a restore check. Do not rely on a development chat session for continuous hosting.

Test closed-candle timing, fee/rounding calculations, reservations, isolation, risk rejections, stale data, pause behavior, rollback, and restart deduplication. Future live and multi-instance milestones need dedicated recovery/isolation tests. Reuse small proven functions/tests from crow-trading without copying its daily scanner architecture.
