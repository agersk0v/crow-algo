# Agent instructions

Read [product](docs/product.md), [architecture](docs/architecture.md), [implementation](docs/implementation.md), and [README](README.md) before working. Follow their current scope; distinguish implemented features, plans, and unresolved decisions.

## Documentation

Only these five documentation files are permitted. New files require an explicit user instruction; expand existing sections instead.

| File | Purpose |
| --- | --- |
| `README.md` | Introduction, current capabilities, verified setup/run/test/backup/restore commands |
| `docs/product.md` | User-facing requirements, behavior, controls, scope, exclusions |
| `docs/architecture.md` | Components, packages/data sources, interfaces, persistence, security, deployment design, technical decisions |
| `docs/implementation.md` | Milestones, tasks, dependencies, acceptance checks, unresolved-decision owners, progress |
| `AGENTS.md` | Contribution rules, documentation ownership, testing, collaboration, PR workflow |

- Every PR reviews all five files for impact and updates affected ones. Remove obsolete/duplicated text, fix links, and verify operating commands. If no edits are needed, state that in the PR; avoid cosmetic changes solely to satisfy this rule.
- Give each topic one authoritative home; summarize briefly and link elsewhere. Keep temporary investigations/discussions in issues/PRs, retaining only useful decisions and rationale in documentation.
- Resolve open behavior in its implementing PR before merge: behavior belongs in product, technical decisions in architecture, and task ownership/progress in implementation. Unrelated open decisions do not block work.
- Mark tasks complete only after acceptance checks pass; report verification and limitations in the PR.
- Do not add nested agent files, standalone plans/reports/guides, or generated documentation. Comments/docstrings, tests, configuration, lockfiles, and operational data are permitted.

## Scope, judgment, and decisions

- Do not expand scope merely because an alternative or future feature is mentioned. Distinguish discussion, an agreed requirement, and authorization to implement.
- Prefer the simplest design meeting the current milestone while preserving agreed extension points. Avoid premature abstractions, services, dependencies, and generic plugin frameworks. Reuse proven crow-trading logic selectively without inheriting its architecture.
- Push back on unnecessary complexity, unsound choices, or conflicts with product goals. Explain the concern, offer alternatives, recommend one, and state tradeoffs; respect the user's informed choice within applicable safety constraints.
- When preparing issues/PRs, identify unresolved architectural decisions. Ask before changing documented architecture, adding major dependencies/services, or committing to significant security, operational, or maintenance consequences. Continue independent work while waiting; routine choices within the agreed architecture need no confirmation.
- Before creating an issue/PR, check that scope is cohesive and reviewable. Push back on independently deliverable changes bundled together or work spanning several milestones; propose smaller deliverables with acceptance checks/dependencies and a parent issue when useful. Do not split tightly coupled work just to reduce size.

## Implementation and verification

- Inspect relevant code/tests first and preserve unrelated user work. Keep strategy, risk, execution, storage, and presentation separate with focused modules.
- Follow the crow-fitness-style layout: backend code/tooling in `backend/`, future UI in `frontend/`, documentation in `docs/`, and operational smoke checks in `scripts/`. Group Python modules by responsibility; add directories only when they contain implemented code.
- Use Python 3.12+, typed interfaces, pinned dependencies, and deterministic tests.
- Test meaningful risks: financial arithmetic, budget limits, order lifecycle, duplicate prevention, recovery, security, and integration boundaries. Avoid tests mirroring implementation, trivial framework behavior, or cosmetic changes; prioritize useful coverage over test counts/percentages.
- Run applicable lint, format, type, and test checks. Report failures and checks not run; do not weaken safeguards to simplify code.

## Trading and communication

- Assume no prior trading knowledge. Explain unfamiliar terms with plain language and concrete examples; make financial consequences and unresolved assumptions clear before requesting a decision.
- Distinguish software correctness, simulated performance, and evidence of a trading advantage. Never fabricate market data, fills, balances, or performance.
- Paper-only until explicitly authorized to implement/activate live trading. Credentials, questions, illustrative amounts, and discussion are not trading permission.
- Follow product exclusions: no leverage, margin, shorts, derivatives, or automatic deposits/withdrawals.
- Keep budgets, allocations, sizing, and risk limits configurable; enforce allocation isolation, available funds, fees, precision, minimums, freshness, and duplicate prevention.
- Preserve closed-candle evaluation, atomic financial writes, and restart reconciliation. Never delete financial records or reset accounts as incidental cleanup.
- Never commit/log secrets. Deployment, scheduled-service activation, and external notifications require user authorization.

## Git workflow

Use a feature branch and linked issue/PR for implementation; never push implementation directly to main. Never merge or enable auto-merge; the user merges. Repository settings and releases require an explicit request. The initial documentation bootstrap was explicitly authorized on main.
