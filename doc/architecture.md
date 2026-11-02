# Architecture

## Shape

One Python trading application, one SQLite database, and a web dashboard on one server. Keep strategy, market data, risk, execution, persistence, and presentation separate. Avoid distributed services and a general plugin framework.

Flow: market data → strategy signal → allocation/risk checks → order intent → execution/reconciliation → persisted state → dashboard.

This is a planned architecture; nothing is implemented yet.

## Major packages and data sources

These are planned dependencies, not packages already installed in this specification-only repository. Pin versions in the appropriate lockfiles when implementation begins.

| Package or component | Responsibility | Source of data |
| --- | --- | --- |
| CCXT (Python) | Exchange adapter for candles, bid/ask quotes, market metadata, and later private order/balance operations | Initially Kraken's public REST API; additional exchanges through explicit adapters/configuration |
| FastAPI + Pydantic | Backend HTTP API and typed validation of settings, controls, and responses | Persisted bot state and validated user input |
| Uvicorn | Run the FastAPI application with one worker | No market data; hosts the API and application lifecycle |
| Python sqlite3 + SQLite | Transactions, persisted accounting, configuration, and activity history | Bot decisions, execution results, and validated market observations |
| Python Decimal and logging | Precise monetary arithmetic and structured operational logging | Application calculations and events; no external data feed |
| Next.js + React + TypeScript | Dashboard, routing, and typed frontend components | FastAPI responses; no direct exchange calls or database access |
| Tailwind CSS + shadcn/ui | Styling and accessible UI components | Presentation only |
| TradingView Lightweight Charts | Render candle/equity charts and trade markers | Data supplied by our backend; the chart library does not supply prices or TradingView market feeds |
| Docker Compose | Build/start frontend and backend, network them, and attach persistent storage | Infrastructure only |

### Crypto information

Kraken is the initial source of truth for the BTC/EUR market; CCXT is the client library, not an independent price provider. Fetch OHLCV through `fetch_ohlcv`, current bid/ask through a supported `fetch_ticker` or `fetch_order_book` endpoint, and symbol/precision/minimum metadata through `load_markets`. Verify the selected endpoint's fields, timestamp semantics, and supported intervals during implementation.

Store exchange identity, market, interval, candle timestamps, observation time, and provider timestamps when available. Reject incomplete candles, invalid/stale quotes, and unsupported/missing metadata rather than silently substituting another exchange's prices. Record local request/receipt times when the provider supplies no timestamp; do not invent a provider timestamp. Validate history coverage because exchange OHLCV endpoints can limit accessible history; pagination does not guarantee unlimited history.

Read-only public market data requires no trading credentials. Future live balances, orders, and fills come from the selected exchange's authenticated API and must be reconciled; paper balances and fills are generated locally and labelled simulated. Public market metadata may not include account-specific fee tiers: configure explicit paper fee assumptions and verify actual fees/market restrictions before live use.

Use REST polling initially with CCXT rate limiting and bounded retries. WebSocket clients, external aggregators, news feeds, paid feeds, pandas, and technical-analysis frameworks are not required initially. Add a dependency only for a concrete need, and update this section when the actual stack changes.

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

## GUI

Use Next.js + TypeScript for the frontend and FastAPI for the backend, using the packages described above.

Build a responsive dashboard: overview, positions/orders/trades, strategy configuration, and logs. Add market/strategy/mode filters as multiple instances arrive. Show stale data and paper/live mode prominently.

Run Next.js and the Python backend as separate Compose services. Route browser API calls through a same-origin /api path to FastAPI; keep backend addresses internal to the Compose network. Use short polling initially; add server-sent events for logs/status only if needed. Next.js must not execute trading logic or own financial storage. Keep trading independent of browser sessions, UI requests, and frontend restarts.

The backend validates configuration and records commands for the trading loop; the browser never accesses SQLite or exchange credentials directly. Authenticate access, protect write requests against CSRF when using cookies, and avoid unsafe rendering of log/provider text.

## Docker Compose and hosting

Docker Compose is the standard startup workflow on one server:

- `frontend`: production Next.js build, serving the dashboard and forwarding /api requests to the backend.
- `backend`: FastAPI plus one supervised trading loop in a single application process. Use exactly one API worker and no development auto-reload so startup cannot launch duplicate trading loops.
- One named data volume mounted only by the backend for SQLite and durable application history. The frontend has no database or exchange-secret access.
- Health checks for both services; the frontend waits for backend readiness on initial startup. Health/readiness distinguishes unavailable or stale trading data from an HTTP server merely responding.
- `restart: unless-stopped` and graceful shutdown, with reconciliation before resumed order processing. Restart policies recover exited containers; an unhealthy check alone does not restart a process.
- Structured stdout/stderr logs with bounded Docker log rotation, plus durable searchable operational history for the dashboard.
- Ignored local configuration and runtime secret injection; never bake credentials into images, commit them, or expose them through browser-visible Next.js variables.

Expose the dashboard only on localhost by default. Public hosting adds HTTPS and authentication before exposing it. Use SQLite-consistent backups to separate storage and verify restore. Normal Compose shutdown/rebuild must preserve data; deleting volumes is never routine cleanup.

Pin container/runtime versions and add Compose/Docker build files when runnable services exist. Do not add Kubernetes or extra database/queue services. Do not rely on a development chat session for continuous hosting.

Test closed-candle timing, fee/rounding calculations, reservations, isolation, risk rejections, stale data, pause behavior, rollback, and restart deduplication. Future live and multi-instance milestones need dedicated recovery/isolation tests. Reuse small proven functions/tests from crow-trading without copying its daily scanner architecture.
