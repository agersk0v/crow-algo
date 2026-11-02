# Agent instructions

## Read first

Read [doc/product.md](doc/product.md), [doc/architecture.md](doc/architecture.md), [doc/implementation.md](doc/implementation.md), and [README.md](README.md). They define the intended bot. Distinguish planned features from implemented behavior.

## Documentation ownership and limits

These are the only five permitted documentation files. Each has a specific purpose:

| File | Owns | Keep elsewhere |
| --- | --- | --- |
| `README.md` | Project introduction, current capabilities, and verified setup/run/test/backup/restore commands | Detailed requirements, architecture, and task lists |
| `doc/product.md` | User-facing requirements, behavior, controls, scope, and exclusions | Package choices, deployment mechanics, and implementation checklists |
| `doc/architecture.md` | Components, packages/data sources, interfaces, persistence, security, deployment design, and technical decisions | Milestone progress, detailed test checklists, and operating commands |
| `doc/implementation.md` | Delivery order, tasks, dependencies, acceptance checks, unresolved-decision owners, and actual progress | Duplicated product specifications or architecture explanations |
| `AGENTS.md` | Contributor rules, document ownership/maintenance, testing obligations, and PR workflow | Detailed product behavior and technical design |

Do not create additional documentation files without an explicit user instruction. Expand sections within these files instead. Do not add nested agent instructions, standalone plans, investigation reports, changelogs, guides, or generated documentation in another format. Source-code comments/docstrings, tests, configuration, lockfiles, and operational data are permitted.

## Documentation maintenance

- Every PR must review all five documents for impact and clean up the affected files: update changed behavior/status, remove obsolete or duplicated text, fix links, and keep operating commands verified.
- Each topic has one authoritative home according to the table. Other documents may give a short overview and link to it; do not repeat detailed rules, package inventories, or procedures.
- Distinguish implemented behavior, planned work, and unresolved decisions. Do not describe a proposed feature or command as working.
- Resolve open behavior in the PR implementing it, before merge: document the resulting behavior in product and technical choices in architecture, then test it. Track the owning milestone in implementation. Unrelated open decisions do not block foundation work.
- Mark implementation tasks complete only when their acceptance checks pass; state validation evidence and any limitations in the PR. Never mark planned work complete merely because code was written.
- Replace outdated text instead of continually appending history. Keep temporary investigations and lengthy design discussions in the issue/PR; retain only decisions and reasoning needed to maintain the system.
- Keep documentation concise and expand only for a concrete requirement or implementation change. Add new files only when explicitly instructed by the user.
- If review finds no documentation changes necessary, say so in the PR description. Do not make cosmetic edits solely to satisfy this rule.

## Scope and implementation

- Do not expand scope merely because an alternative or future feature is mentioned. Distinguish discussion, an agreed requirement, and authorization to implement.
- Start with one spot pair and one paper strategy instance on hourly candles, but use explicit market, strategy-instance, allocation-account, and execution-mode identities so future multiple markets, strategies, and live execution fit the same core.
- Keep Python modules focused. Keep strategy, risk, execution, storage, and presentation separate without adding unnecessary abstraction.
- Add strategies through the common interface; do not build a general plugin framework.
- Reuse proven logic selectively from crow-trading. Do not inherit its architecture or expand scope incidentally.
- Preserve unrelated user work. Inspect relevant code and tests before editing.
- Use Python 3.12+, typed interfaces, pinned dependencies, and deterministic tests.
- Run applicable lint, formatting, type, and test checks. Report failures and checks not run.

## Focused testing

Write tests that protect meaningful behavior and risks: financial calculations, budget limits, order lifecycle, duplicate prevention, recovery, security, and important integration boundaries. Avoid tests that merely mirror implementation, trivial framework behavior, or cosmetic changes. Prefer a small, effective test suite over maximizing test count or coverage percentages.

## Collaboration and trading explanations

Exercise independent judgment. If a request appears unnecessarily complex, technically unsound, or inconsistent with the product goals, explain the concern plainly. Offer practical alternatives, recommend one, and describe the tradeoffs. Do not agree automatically. Respect the user's informed choice within applicable safety constraints.

Assume no prior trading knowledge. Explain unfamiliar terms in plain language with concrete examples. Distinguish software correctness, simulated performance, and evidence of a trading advantage. Make financial consequences and unresolved assumptions clear before asking for a decision. Never treat a question, illustrative amount, or discussion of live trading as authorization to trade.

## Trading and records

- Paper trading only until the user explicitly requests live implementation/activation. Credentials alone are not authorization.
- No leverage, margin, shorts, derivatives, deposits, or withdrawals.
- Budgets, strategy allocations, purchase sizes, and risk limits are configurable; never hardcode a monetary cap. Keep allocations separate and enforce shared available-funds checks.
- Enforce fees, precision, minimum orders, budget caps, freshness, and duplicate prevention.
- Preserve closed-candle evaluation, atomic financial writes, and restart reconciliation.
- Never log or commit secrets. Never fabricate market data, fills, balances, or performance.
- Never delete financial records or reset an account as incidental cleanup.
- Do not deploy, activate scheduled services, or send external notifications without user authorization.

## Architectural decisions

When preparing an issue or PR, identify unresolved architectural decisions. If a decision changes the documented architecture, introduces a major dependency or service, or has significant security, operational, or maintenance consequences, ask the user before committing to it. Explain the options, recommend one, and describe the tradeoffs. Continue independent work while awaiting an answer. Routine implementation choices consistent with the agreed architecture do not require confirmation.

## Git workflow

The initial documentation bootstrap is authorized directly on main. For subsequent implementation, use a feature branch and a linked issue/pull request. Do not push implementation directly to main. Never merge a pull request or enable auto-merge; the user merges. Do not change repository settings or publish releases without an explicit request.
