"""Small contracts for future implementations; no adapters or registry yet."""

from datetime import datetime
from typing import Protocol

from pydantic import JsonValue

from crow_algo.domain import Candle, Market, OrderIntent, OrderStatus, Signal


class Strategy(Protocol):
    def evaluate(
        self,
        market: Market,
        candles: tuple[Candle, ...],
        parameters: dict[str, JsonValue],
        *,
        as_of: datetime,
    ) -> Signal:
        """Use validated closed candles; sizing and execution belong elsewhere."""
        ...


class Execution(Protocol):
    def submit(self, intent: OrderIntent) -> OrderStatus: ...

    def reconcile(self, order: OrderStatus) -> OrderStatus: ...

    def cancel(self, order: OrderStatus) -> OrderStatus: ...
