# Product

Defines intended user-facing trading behavior and scope. Configuration validation exists; operational trading features remain planned. Delivery status and unresolved-decision ownership live in [implementation](implementation.md).

## Goal

Run a crypto bot continuously with configurable capital, understandable decisions, and a dashboard showing what it is doing. Start small while supporting future multiple markets, strategies, and live trading. No profitability is promised.

## Initial release

- Kraken BTC/EUR spot trading; one momentum strategy instance using completed hourly candles.
- Paper execution with public bid/ask quotes observed after the decision, explicit fees/slippage, precision, and exchange minimums.
- Configurable total budget, strategy allocation, purchase amount, maximum position/exposure, and loss thresholds. There is no fixed monetary cap.
- Long-only, initially at most one position per strategy/market and no additional buys while an entry or position exists.
- Initial market, strategy, parameters, and timeframe are configuration rather than hardcoded assumptions.

## Momentum v1 rules

The offline strategy compares completed closing prices: `(latest close / close N candles earlier - 1) × 100`. Configurable parameters are `lookback` (positive integer, default 24 candles), `entry_threshold_pct` (default +2), and `exit_threshold_pct` (default −1). Thresholds accept finite decimal strings or integers, not binary floats or booleans; exit must be strictly below entry. Unknown parameters are errors.

Return `enter_long` strictly above the entry threshold, `exit_long` strictly below the exit threshold, and `hold` between them, including equality. For an earlier close of €100, latest closes of €103, €101, and €98 produce entry, hold, and exit respectively; €102 and €99 are exact boundaries and hold. These are continuing conditions, not crossing-only events. Every decision explains the price comparison or lack of history.

N intervals require N + 1 completed candles: the default needs 25 hourly candles spanning 24 hours between closing prices. Insufficient valid history returns hold with a reason. Only candles closed at or before the supplied evaluation time count. Reject duplicate, out-of-order, or overlapping completed history; within the latest required window (or all available candles when short), also reject gaps and inconsistent candle durations. Do not repair or invent history. Older gaps outside that window do not affect the calculation.

A signal does not place an order. Future runner/risk checks must prevent repeated buys while an entry or position exists and sales of another strategy's holdings. Hold keeps the current state, whether cash or crypto. Candle freshness, scheduling, and missed-signal recovery remain responsibilities of the future runner.

These defaults are starting assumptions, not optimized settings or evidence of profitability. Fees and sideways markets can cause losses. The exit threshold measures momentum from a historical close, not loss from a purchase price; it is not a stop-loss guarantee. Loss limits are separate risk controls.

## Extension requirements

- A market is an exchange, market type, and trading pair. Start with spot markets.
- A strategy instance has its own ID, strategy type/version, parameters, markets, timeframe, execution mode, and budget allocation.
- Allow additional markets and strategy instances through the same core interfaces; concurrent multi-market/strategy operation follows the initial release.
- Maintain separate strategy cash, reservations, positions, fees, and results. Shared exchange funds must not be allocated twice.
- One strategy must not sell another's position in the same coin. Record ownership internally even if exchange balances are aggregated.
- Start with a shared quote currency; do not add unlike currencies or present combined equity without explicit conversion data.
- Paper and live accounts have separate state and balances. Changing mode does not convert a paper position into a real one.
- Live execution is a planned later milestone, not permanently excluded.

## Budgets and configuration

The user explicitly sets capital and allocations. Sum of strategy allocations cannot exceed the available bot budget; pending orders and fees count against spendable funds. Future live spending is also bounded by reconciled exchange balances.

Record configuration versions and allocation changes with effective times. A budget increase is not a deposit; paper funding changes are separate recorded events, and live funding comes only from verified exchange balances. Reject reductions below committed capital rather than silently selling positions. Restart never resets balances.

Pause affected strategy instances and require no position or pending order for strategy/timeframe identity changes initially. Existing orders retain their configuration version. Validate and audit all dashboard changes.

## Dashboard and controls

Show running/paused/degraded/error state, execution mode, heartbeat, last successful data update, price freshness, cash, reservations, positions, equity history, fees, and realized/unrealized results. Show decisions with reasons, order states, fills, and searchable operational logs. Support filters by market, strategy instance, and mode as those capabilities arrive.

Configure budgets, strategy parameters, and enabled markets through validated forms. Pause blocks new entries while monitoring and exits continue. Process shutdown stops all processing without liquidation. Risk-halt behavior must be explicit; resuming must not silently clear a latched risk halt.

## Reliability and live operation

The application must run continuously on one cloud server with automatic restart, persistent storage, authenticated dashboard access, backups, and a verified restore. Technical hosting design is defined in [architecture](architecture.md#docker-compose-and-hosting). Closing/restarting the frontend must not stop trading. Refuse new entries for stale data, insufficient funds, or failed reconciliation.

Future live execution requires explicit activation, credentials without withdrawal permissions, partial-fill accounting, cancellation handling, and reconciliation of uncertain submissions before retry. Manual/external exchange activity must be detected and handled, not assigned to a strategy arbitrarily.

## Outside current scope

Stocks, derivatives, margin, shorts, automatic deposits/withdrawals, visual strategy builders, distributed services, and a full research platform.

## Requirements awaiting definition

Loss-halt policy, outage recovery, accounting terminology, authentication, and paper order lifecycle will be defined in their implementing PRs. [Implementation](implementation.md#open-decisions-and-owning-milestones) assigns each decision to a milestone; this file will own the resulting user-visible behavior.
