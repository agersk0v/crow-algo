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

Detailed strategy rules, loss-halt policy, outage recovery, accounting terminology, authentication, and paper order lifecycle will be defined in their implementing PRs. [Implementation](implementation.md#open-decisions-and-owning-milestones) assigns each decision to a milestone; this file will own the resulting user-visible behavior.
