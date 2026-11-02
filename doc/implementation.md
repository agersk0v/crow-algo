# Implementation

Status: local foundation implemented through configuration/contracts, PostgreSQL persistence/migrations, ownership primitive, and health-only API/Compose. Trading, GUI, and production operation remain planned. Implement in small linked issues/PRs, updating this file with actual progress and verification.

## Open decisions and owning milestones

Resolve each item in the implementing PR before merge, with explicit behavior, documentation, and tests. These decisions do not block unrelated foundation work. Product owns user-facing outcomes; architecture owns technical choices.

| Decision | Owning milestone |
| --- | --- |
| Momentum entry/exit formulas, lookbacks, and insufficient-history behavior | 2: offline paper core |
| Funding/allocation, purchase size, exposure limits, accounting terms, and treatment of funding in performance | 2: offline paper core |
| Loss-threshold calculation, action on breach, and clearing a halt | 2: offline paper core |
| Missing-quote behavior, paper order expiry/cancellation, fee/slippage assumptions | 2: offline paper core; validate provider assumptions in 3 |
| Missed candles, signal eligibility after outages, freshness limits, and quote polling cadence | 3: public-market operation |
| Owner authentication, sessions, API enforcement, and write-request protection | 4: GUI, before exposure |
| Hosting provider, backup schedule/retention, and deployment configuration | 5: continuous hosting |

## 1. Foundation and domain

Tracked by [#1](https://github.com/agersk0v/crow-algo/issues/1), delivered sequentially through #2 (contracts/configuration), #3 (PostgreSQL), and #4 (API/Compose).

- [x] Set up Python 3.12+, pinned dependencies, lint/format/type/test commands, and CI workflow.
- [x] Add PostgreSQL configuration persistence using SQLAlchemy 2, Psycopg 3, and Alembic migrations (#3).
- [x] Add isolated PostgreSQL integration tests for migrations, rollback, schema/role constraints, duplicate-owner rejection, release, and ownership loss.
- [x] Add the local PostgreSQL/backend Compose setup and health endpoints (#4). Financial allocation/reservation locking follows in milestone 2 when those records exist.
- [x] Add pinned non-root application image, one-shot migration/grant step, runtime secrets, health checks, and graceful lifecycle.
- [x] Define market, strategy-instance, allocation/execution-account/mode, configuration-version, order, and fill identities.
- [x] Define small strategy/execution interfaces and validate configuration without hardcoded pair, interval, or budget.

Acceptance: validated configuration can describe multiple markets/instances, while eligibility checks permit one paper instance. Invalid allocations and unsupported activation fail clearly. The foundation API does not run trading.

Issue #2 adds contracts/eligibility validation; #3 adds append-only configuration snapshots and an ownership primitive; #4 adds local startup and read-only health checks. Verification includes schema mismatch, API responsiveness during blocked probes, database outage/recovery, restart/down-up persistence, and no implicit funding/trading. Evidence belongs in each PR; CI must pass before merge.

## 2. Offline paper core

Depends on milestone 1.

- [ ] Resolve the strategy, accounting, loss-limit, and paper-order decisions assigned above.
- [ ] Implement one momentum strategy, sizing/risk checks, reservations, and paper execution.
- [ ] Persist decisions/reasons, orders/fills, balances, configuration history, quote evidence, and equity samples.
- [ ] Keep budget/allocation changes explicit; distinguish limits from actual capital/funding.
- [ ] Implement pause, risk halt, transaction rollback, and restart reconciliation.

Acceptance: deterministic buy/hold/sell exercise verifies fees, balance changes, minimum orders, stale data, budget rejection, and restart without duplicate funding/orders.

## 3. Public-market operation

Depends on milestone 2.

- [ ] Define and test missed-candle handling, eligible signals after outages, quote freshness, and polling cadence.
- [ ] Add CCXT candles, bid/ask quotes, market precision/minimums, freshness checks, and rate limits.
- [ ] Run the initial hourly BTC/EUR instance; intervals and pair remain configurable.
- [ ] Add the sequential loop, durable structured logs, heartbeat, bounded retries, and order recovery.
- [ ] Paper buys use ask and sells bid after the decision; do not double-charge spread.

Acceptance: public-data paper operation resumes after interruption and rejects stale/incomplete input without inventing fills. Trading runs without a browser connection.

## 4. GUI

Depends on persisted state/API contracts from milestones 2–3; a read-only shell may be developed earlier.

- [ ] Define owner authentication/session handling and enforce access at the API, including write-request protection.
- [ ] Build the Next.js + TypeScript frontend with Tailwind/shadcn and Lightweight Charts, backed by FastAPI.
- [ ] Build authenticated overview, equity/candle charts, position/order/trade tables, decisions, and searchable logs.
- [ ] Add validated settings and acknowledged pause/resume controls, recording configuration versions.
- [ ] Show mode, freshness, reservations, health, fees, and realized/unrealized results.

Acceptance: displayed amounts match the ledger; errors and rejected commands are visible; UI refresh/retry cannot duplicate trading actions. Use backend filtering/pagination for growing history.

## 5. Docker Compose and continuous hosting

Production acceptance depends on milestones 3–4; add local Compose infrastructure earlier as services become runnable.

- [x] Package the local backend/database with a separate migration step; no frontend or trading loop yet.
- [ ] Add Next.js and its internal API connection when the GUI is runnable.
- [ ] Run one backend process/API worker and one trading-loop owner; keep trading independent of frontend restarts.
- [x] Add database-owned persistent storage, database/backend health checks, one migration step, graceful shutdown, restart policies, and bounded container logs. Database port is internal.
- [ ] Add frontend health checks with the GUI.
- [x] Verify local Compose configuration/build/startup, health endpoints, database outage/recovery, and record retention across restart/down-up.
- [ ] Verify frontend API routing and trade-safe restart after those features exist.
- [ ] Choose one server; configure HTTPS/authentication, secrets injection, and off-volume backup storage.
- [ ] Add automatic pg_dump backups to separate storage and a verified pg_restore procedure in README.md; do not copy a live database volume as a backup.
- [ ] Verify restart, disk persistence, restore, and log rotation independently of trade retention.

Acceptance: docker compose up -d --build starts the application; frontend restart leaves trading running, and backend/database restart and normal down/up preserve state and reconcile without resetting capital or replaying trades. Verify backup restore separately. Do not use volume deletion as cleanup. Deploy only when authorized.

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

## Verification

Use PostgreSQL integration tests for migrations, constraints, transactions, allocation locking, ownership loss, and restart recovery. Test closed-candle timing, fee/rounding calculations, reservations, risk rejections, stale data, pause behavior, rollback, and restart deduplication. Multi-instance and live milestones add dedicated isolation and exchange-recovery tests.

Verify that blocking exchange/database calls cannot freeze API requests and that a lost ownership connection stops the trading loop. Reuse small proven safety tests from crow-trading where appropriate. Keep validation evidence in PRs; mark a task complete only after its acceptance checks pass.

## Scope discipline

Update these milestones instead of creating more planning documents. Do not implement future features prematurely, but preserve their account/market/strategy identities and interfaces from the foundation. Tests prove software behavior, not investment performance.
