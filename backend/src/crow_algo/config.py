"""Declarative configuration is separate from supported activation."""

from collections.abc import Sequence
from fractions import Fraction
from typing import Annotated, Literal

from pydantic import Field, JsonValue, model_validator

from crow_algo.domain import (
    Amount,
    Currency,
    Identifier,
    Market,
    Mode,
    Record,
    Timeframe,
    Version,
)


class ExecutionAccount(Record):
    id: Identifier
    exchange: Identifier
    mode: Mode
    quote_currency: Currency
    budget: Amount


class AllocationAccount(Record):
    id: Identifier
    execution_account_id: Identifier
    budget: Amount


class StrategyInstance(Record):
    id: Identifier
    strategy_type: Identifier
    strategy_version: Version
    parameters: dict[str, JsonValue] = Field(default_factory=dict)
    market_ids: Annotated[tuple[Identifier, ...], Field(min_length=1)]
    timeframe: Timeframe
    allocation_account_id: Identifier


class Configuration(Record):
    schema_version: Literal[1] = 1
    version: Version
    markets: Annotated[tuple[Market, ...], Field(min_length=1)]
    execution_accounts: Annotated[tuple[ExecutionAccount, ...], Field(min_length=1)]
    allocation_accounts: Annotated[tuple[AllocationAccount, ...], Field(min_length=1)]
    strategies: Annotated[tuple[StrategyInstance, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def references_and_budgets(self) -> "Configuration":
        for name in (
            "markets",
            "execution_accounts",
            "allocation_accounts",
            "strategies",
        ):
            items = getattr(self, name)
            if len({item.id for item in items}) != len(items):
                raise ValueError(f"duplicate IDs in {name}")

        markets = {item.id: item for item in self.markets}
        identities = {
            (m.exchange, m.market_type, m.base, m.quote) for m in self.markets
        }
        if len(identities) != len(markets):
            raise ValueError("duplicate market identities")
        executions = {item.id: item for item in self.execution_accounts}
        allocations = {item.id: item for item in self.allocation_accounts}
        if len({account.quote_currency for account in self.execution_accounts}) != 1:
            raise ValueError("configuration requires a shared quote currency")

        # Validation must not round totals through Decimal's arithmetic context.
        totals = dict.fromkeys(executions, Fraction())
        for allocation in self.allocation_accounts:
            if allocation.execution_account_id not in executions:
                raise ValueError("allocation references an unknown execution account")
            totals[allocation.execution_account_id] += Fraction(allocation.budget)
        for execution in self.execution_accounts:
            if totals[execution.id] > Fraction(execution.budget):
                raise ValueError("allocations exceed execution account budget")

        used_allocations: set[str] = set()
        for strategy in self.strategies:
            if strategy.allocation_account_id not in allocations:
                raise ValueError("strategy references an unknown allocation account")
            if strategy.allocation_account_id in used_allocations:
                raise ValueError("strategies must have separate allocation accounts")
            used_allocations.add(strategy.allocation_account_id)
            if len(set(strategy.market_ids)) != len(strategy.market_ids):
                raise ValueError("strategy has duplicate market references")
            execution = executions[
                allocations[strategy.allocation_account_id].execution_account_id
            ]
            for market_id in strategy.market_ids:
                if market_id not in markets:
                    raise ValueError("strategy references an unknown market")
                market = markets[market_id]
                if (market.exchange, market.quote) != (
                    execution.exchange,
                    execution.quote_currency,
                ):
                    raise ValueError("market exchange/currency does not match account")
        return self


class UnsupportedActivation(ValueError):
    """A valid configuration requests capabilities not implemented yet."""


def validate_activation(
    config: Configuration, strategy_instance_ids: Sequence[str]
) -> StrategyInstance:
    """Check initial-release eligibility only; never start or fund anything."""
    if len(strategy_instance_ids) != 1:
        raise UnsupportedActivation("initial release requires exactly one strategy")
    strategy = next(
        (s for s in config.strategies if s.id == strategy_instance_ids[0]), None
    )
    if strategy is None:
        raise UnsupportedActivation("unknown strategy instance")
    if len(strategy.market_ids) != 1:
        raise UnsupportedActivation("initial release requires exactly one market")
    if (strategy.strategy_type, strategy.strategy_version) != ("momentum", 1):
        raise UnsupportedActivation("initial release supports momentum version 1 only")
    allocation = next(
        a for a in config.allocation_accounts if a.id == strategy.allocation_account_id
    )
    account = next(
        a for a in config.execution_accounts if a.id == allocation.execution_account_id
    )
    if account.mode != "paper":
        raise UnsupportedActivation("live activation is not supported")
    return strategy
