# Agent instructions

## Read first

Read [PRODUCT.md](PRODUCT.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [README.md](README.md). They define the intended bot. Distinguish planned features from implemented behavior.

## Documentation limit

**Do not create any additional documentation files.** The only permitted documentation files are these four files at the repository root:

- `AGENTS.md`
- `PRODUCT.md`
- `ARCHITECTURE.md`
- `README.md`

Update the appropriate existing file instead. Do not add a docs directory, nested agent instructions, standalone plans, implementation reports, changelogs, guides, or documentation in another format. Do not generate or commit documentation artifacts. This does not prohibit source-code comments/docstrings, tests, configuration, lockfiles, or operational data. Changes to this limit require an explicit user instruction.

## Scope and implementation

- Build the smallest implementation that satisfies the product: one spot pair, one active strategy, one account, hourly candles, and paper execution first.
- Keep Python modules focused. Keep strategy, risk, execution, storage, and presentation separate without adding unnecessary abstraction.
- Add strategies through the common interface; do not build a general plugin framework.
- Reuse proven logic selectively from crow-trading. Do not inherit its architecture or expand scope incidentally.
- Preserve unrelated user work. Inspect relevant code and tests before editing.
- Use Python 3.12+, typed interfaces, pinned dependencies, and deterministic tests.
- Update these existing documents when behavior changes. Keep setup and operation commands in README.md accurate and verified.
- Test meaningful behavior changes and run applicable lint, formatting, type, and test checks. Report failures and checks not run.

## Trading and records

- Paper trading only until the user explicitly requests live implementation/activation. Credentials alone are not authorization.
- No leverage, margin, shorts, derivatives, deposits, or withdrawals.
- The initial €50 is the total account budget, not a per-trade amount.
- Enforce fees, precision, minimum orders, budget caps, freshness, and duplicate prevention.
- Preserve closed-candle evaluation, atomic financial writes, and restart reconciliation.
- Never log or commit secrets. Never fabricate market data, fills, balances, or performance.
- Never delete financial records or reset an account as incidental cleanup.
- Do not deploy, activate scheduled services, or send external notifications without user authorization.

## Git workflow

The initial documentation bootstrap is authorized directly on main. For subsequent implementation, use a feature branch and a linked issue/pull request. Do not push implementation directly to main. Never merge a pull request or enable auto-merge; the user merges. Do not change repository settings or publish releases without an explicit request.
