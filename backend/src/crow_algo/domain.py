"""Shared value types and messages; no exchange, clock, or storage access."""

from datetime import UTC
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

Identifier = Annotated[
    str, StringConstraints(strict=True, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
]
Currency = Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Z0-9]+$")]
Timeframe = Annotated[
    str, StringConstraints(strict=True, pattern=r"^[1-9][0-9]*[mhdw]$")
]
Version = Annotated[int, Field(strict=True, gt=0)]
Mode = Literal["paper", "live"]
Side = Literal["buy", "sell"]


def exact_amount(value: object) -> Decimal:
    """Accept decimal strings/integers, never binary floats or booleans."""
    if isinstance(value, bool) or not isinstance(value, str | int | Decimal):
        raise ValueError("amount must be a decimal string, integer, or Decimal")
    try:
        amount = Decimal(value)
    except ArithmeticError as exc:
        raise ValueError("invalid decimal amount") from exc
    if not amount.is_finite():
        raise ValueError("amount must be finite")
    return amount


Amount = Annotated[Decimal, BeforeValidator(exact_amount), Field(ge=0)]
PositiveAmount = Annotated[Decimal, BeforeValidator(exact_amount), Field(gt=0)]
Timestamp = Annotated[
    AwareDatetime, AfterValidator(lambda value: value.astimezone(UTC))
]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Market(Record):
    id: Identifier
    exchange: Identifier
    market_type: Literal["spot"] = "spot"
    base: Currency
    quote: Currency

    @model_validator(mode="after")
    def distinct_currencies(self) -> "Market":
        if self.base == self.quote:
            raise ValueError("base and quote currencies must differ")
        return self

    @property
    def symbol(self) -> str:
        return f"{self.base}/{self.quote}"


class Candle(Record):
    opened_at: Timestamp
    closed_at: Timestamp
    open: PositiveAmount
    high: PositiveAmount
    low: PositiveAmount
    close: PositiveAmount
    volume: Amount

    @model_validator(mode="after")
    def valid_interval_and_prices(self) -> "Candle":
        if self.opened_at >= self.closed_at:
            raise ValueError("candle open must precede close")
        if (
            not self.low
            <= min(self.open, self.close)
            <= max(self.open, self.close)
            <= self.high
        ):
            raise ValueError("invalid candle OHLC bounds")
        return self


class Signal(Record):
    intent: Literal["enter_long", "exit_long", "hold"]
    reason: Annotated[str, StringConstraints(strict=True, min_length=1)]


class OrderIntent(Record):
    id: Identifier
    strategy_instance_id: Identifier
    execution_account_id: Identifier
    mode: Mode
    market_id: Identifier
    configuration_version: Version
    side: Side
    quantity: PositiveAmount
    created_at: Timestamp


class Fill(Record):
    id: Identifier
    order_intent_id: Identifier
    execution_account_id: Identifier
    mode: Mode
    quantity: PositiveAmount
    price: PositiveAmount
    fee: Amount
    fee_currency: Currency
    executed_at: Timestamp


class OrderStatus(Record):
    order_intent_id: Identifier
    execution_account_id: Identifier
    mode: Mode
    state: Literal["pending", "partial", "filled", "cancelled", "rejected", "unknown"]
    exchange_order_id: str | None = None
