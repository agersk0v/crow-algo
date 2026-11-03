"""Price-change momentum v1, evaluated only from supplied completed candles."""

from datetime import datetime
from decimal import MAX_EMAX, MIN_EMIN, Context, Decimal, localcontext
from itertools import pairwise
from typing import Annotated

from pydantic import BeforeValidator, Field, JsonValue, model_validator

from crow_algo.domain import Candle, Market, Record, Signal, exact_amount

Percentage = Annotated[Decimal, BeforeValidator(exact_amount)]


class MomentumParameters(Record):
    lookback: Annotated[int, Field(strict=True, gt=0)] = 24
    entry_threshold_pct: Percentage = Decimal("2")
    exit_threshold_pct: Percentage = Decimal("-1")

    @model_validator(mode="after")
    def ordered_thresholds(self) -> "MomentumParameters":
        if self.exit_threshold_pct >= self.entry_threshold_pct:
            raise ValueError("exit threshold must be strictly below entry threshold")
        return self


class MomentumStrategy:
    def evaluate(
        self,
        market: Market,
        candles: tuple[Candle, ...],
        parameters: dict[str, JsonValue],
        *,
        as_of: datetime,
    ) -> Signal:
        settings = MomentumParameters.model_validate(parameters)
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        eligible = tuple(candle for candle in candles if candle.closed_at <= as_of)
        # Check ordering before taking the tail: never hide a misplaced latest candle.
        for previous, current in pairwise(eligible):
            if current.opened_at < previous.closed_at:
                raise ValueError(
                    "completed candles must be ordered and non-overlapping"
                )
        window = eligible[-(settings.lookback + 1) :]
        if window:
            interval = window[0].closed_at - window[0].opened_at
            for candle in window:
                if candle.closed_at - candle.opened_at != interval:
                    raise ValueError("required candles must have a consistent interval")
            for previous, current in pairwise(window):
                if current.opened_at != previous.closed_at:
                    raise ValueError("required candles must be consecutive (no gaps)")
        if len(window) < settings.lookback + 1:
            return Signal(
                intent="hold",
                reason=(
                    f"Insufficient history for {market.symbol}: need "
                    f"{settings.lookback + 1} completed candles, have {len(window)}"
                ),
            )

        baseline, latest = window[0].close, window[-1].close
        entry, exit_ = settings.entry_threshold_pct, settings.exit_threshold_pct
        # (latest / baseline - 1) * 100 > threshold is equivalent to
        # (latest - baseline) * 100 > baseline * threshold (baseline > 0).
        # Finite products/subtraction can be exact; division may repeat forever.
        # Size an isolated Decimal context to preserve every input digit and scale.
        precision = 10 + sum(
            len(value.as_tuple().digits) + abs(int(value.as_tuple().exponent))
            for value in (baseline, latest, entry, exit_)
        )
        with localcontext(Context(prec=precision, Emax=MAX_EMAX, Emin=MIN_EMIN)):
            change = (latest - baseline) * 100
            if change > baseline * entry:
                intent = "enter_long"
                comparison = f"above entry threshold {entry}%"
            elif change < baseline * exit_:
                intent = "exit_long"
                comparison = f"below exit threshold {exit_}%"
            else:
                intent = "hold"
                comparison = f"within inclusive hold range [{exit_}%, {entry}%]"
        return Signal(
            intent=intent,
            reason=(
                f"{market.symbol} momentum ({latest} / {baseline} - 1) × 100 "
                f"over {settings.lookback} candles is {comparison}"
            ),
        )
