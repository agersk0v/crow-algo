# Implementation

Status: planning only. All milestones below are incomplete. Implement in small linked issues/PRs, updating this file with actual progress and verification.

## 1. Foundation and domain

- [ ] Agree the initial strategy parameters, configurable funding/allocation, sizing, loss policy, and fee assumptions.
- [ ] Set up Python 3.12+, pinned dependencies, lint/type/test checks, and PostgreSQL persistence using SQLAlchemy 2, Psycopg 3, and Alembic migrations.
- [ ] Add the PostgreSQL Compose service and isolated PostgreSQL integration tests for migrations, rollback, allocation locking, constraints, and duplicate-owner rejection.
- [ ] Keep application entry points compatible with container startup; add Dockerfiles and compose.yaml once runnable services exist.
- [ ] Define market, strategy-instance, execution-account/mode, configuration-version, order, and fill identities.
- [ ] Define small strategy and execution interfaces without hardcoded pair, interval, or budget.

Acceptance: validated configuration can describe multiple markets/instances, while the initial runtime enables one paper instance. Invalid allocations and unsupported combinations fail clearly.

## 2. Offline paper core

- [ ] Implement one momentum strategy, sizing/risk checks, reservations, and paper execution.
- [ ] Persist decisions/reasons, orders/fills, balances, configuration history, quote evidence, and equity samples.
- [ ] Keep budget/allocation changes explicit; distinguish limits from actual capital/funding.
- [ ] Implement pause, risk halt, transaction rollback, and restart reconciliation.

Acceptance: deterministic buy/hold/sell exercise verifies fees, balance changes, minimum orders, stale data, budget rejection, and restart without duplicate funding/orders.

## 3. Public-market operation

- [ ] Add CCXT candles, bid/ask quotes, market precision/minimums, freshness checks, and rate limits.
- [ ] Run the initial hourly BTC/EUR instance; intervals and pair remain configurable.
- [ ] Add the sequential loop, durable structured logs, heartbeat, bounded retries, and order recovery.
- [ ] Paper buys use ask and sells bid after the decision; do not double-charge spread.

Acceptance: public-data paper operation resumes after interruption and rejects stale/incomplete input without inventing fills. Trading runs without a browser connection.

## 4. GUI

- [ ] Build the Next.js + TypeScript frontend with Tailwind/shadcn and Lightweight Charts, backed by FastAPI.
- [ ] Build authenticated overview, equity/candle charts, position/order/trade tables, decisions, and searchable logs.
- [ ] Add validated settings and acknowledged pause/resume controls, recording configuration versions.
- [ ] Show mode, freshness, reservations, health, fees, and realized/unrealized results.

Acceptance: displayed amounts match the ledger; errors and rejected commands are visible; UI refresh/retry cannot duplicate trading actions. Use backend filtering/pagination for growing history.

## 5. Docker Compose and continuous hosting

- [ ] Package Next.js, the Python backend, and PostgreSQL as three Compose services with pinned builds and internal API/database connections.
- [ ] Run one backend process/API worker and one trading-loop owner; keep trading independent of frontend restarts.
- [ ] Add a database-owned persistent volume, database/backend/frontend health checks, one migration step, graceful shutdown, restart policies, and bounded container logs. Do not expose the database port by default.
- [ ] Verify `docker compose config`, image builds, startup, health, API routing, and stop/start without lost records or duplicate trades.
- [ ] Choose one server; configure HTTPS/authentication, secrets injection, and off-volume backup storage.
- [ ] Add automatic pg_dump backups to separate storage and a verified pg_restore procedure in README.md; do not copy a live database volume as a backup.
- [ ] Verify restart, disk persistence, restore, and log rotation independently of trade retention.

Acceptance: docker compose up -d --build starts the application; frontend restart leaves trading running, and backend/database restart and normal down/up preserve state and reconciles without resetting capital or replaying trades. Verify backup restore separately. Do not use volume deletion as cleanup. Deploy only when authorized.

## 6. Multiple markets and strategies

- [ ] Enable several configured markets and strategy instances, initially sharing one quote currency.
- [ ] Share candle fetching, enforce exchange rate limits, and isolate instance budgets, reservations, positions, and results.
- [ ] Enforce shared exposure/available-funds checks; resolve simultaneous signals deterministically.
- [ ] Extend dashboard filters and per-instance controls.

Acceptance: two instances on the same pair cannot spend each other's funds or sell each other's holdings; allocations cannot exceed total funding. No new database or distributed worker is required.

## 7. Live execution

- [ ] Add an explicitly enabled live adapter through the existing execution interface; keep paper/live accounts separate.
- [ ] Verify current exchange permissions, fees, precision, minimums, and supported order semantics.
- [ ] Implement client order IDs, partial fills, cancellation, unknown submission recovery, and exchange reconciliation.
- [ ] Detect external/manual orders, trades, and balance discrepancies; block ambiguous operation.
- [ ] Test with deterministic exchange fixtures and supported sandbox facilities before any separately authorized real order.

Acceptance: ambiguous timeouts and restarts do not duplicate submissions; reconciled balances and ownership bound every order. Live mode is clearly visible and cannot activate from credentials alone.

## Scope discipline

Update these milestones instead of creating more planning documents. Do not implement future features prematurely, but preserve their account/market/strategy identities and interfaces from the foundation. Tests prove software behavior, not investment performance.
