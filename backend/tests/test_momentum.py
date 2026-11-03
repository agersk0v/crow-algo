"""Synthetic strategy cases; these are not market-performance evidence."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Inexact, localcontext

import pytest
from pydantic import JsonValue, ValidationError

from crow_algo.domain import Candle, Market
from crow_algo.interfaces import Strategy
from crow_algo.strategies.momentum import MomentumStrategy

START = datetime(2026, 1, 1, tzinfo=UTC)
MARKET = Market(id="btc", exchange="kraken", base="BTC", quote="EUR")
STRATEGY: Strategy = MomentumStrategy()


def history(
    latest: str = "103", *, count: int = 25, minutes: int = 60, baseline: str = "100"
) -> tuple[Candle, ...]:
    step = timedelta(minutes=minutes)
    return tuple(
        Candle(
            opened_at=START + index * step,
            closed_at=START + (index + 1) * step,
            open=price,
            high=price,
            low=price,
            close=price,
            volume="1",
        )
        for index in range(count)
        for price in [latest if index == count - 1 else baseline]
    )


@pytest.mark.parametrize(
    ("price", "intent", "reason"),
    [
        ("103", "enter_long", "above entry threshold 2%"),
        ("101", "hold", "inclusive hold range"),
        ("98", "exit_long", "below exit threshold -1%"),
        ("102", "hold", "inclusive hold range"),
        ("99", "hold", "inclusive hold range"),
    ],
)
def test_agreed_examples(price: str, intent: str, reason: str) -> None:
    candles = history(price)
    result = STRATEGY.evaluate(MARKET, candles, {}, as_of=candles[-1].closed_at)
    assert result.intent == intent
    assert reason in result.reason
    assert f"({price} / 100 - 1)" in result.reason


@pytest.mark.parametrize("count", [0, 1, 24])
def test_insufficient_history_holds(count: int) -> None:
    result = STRATEGY.evaluate(
        MARKET, history(count=count), {}, as_of=START + timedelta(days=2)
    )
    assert result.intent == "hold"
    assert f"need 25 completed candles, have {count}" in result.reason


def test_eligible_history_and_inputs_are_stable() -> None:
    candles = history(count=26, latest="1")
    parameters: dict[str, JsonValue] = {"lookback": 24}
    original = deepcopy((candles, parameters))
    as_of = candles[24].closed_at
    # The 26th candle opens exactly at as_of and is not completed yet.
    expected = STRATEGY.evaluate(MARKET, candles[:25], parameters, as_of=as_of)
    assert STRATEGY.evaluate(MARKET, candles, parameters, as_of=as_of) == expected
    assert STRATEGY.evaluate(MARKET, candles, parameters, as_of=as_of) == expected
    assert expected.intent == "hold"
    assert (candles, parameters) == original
    # A partially formed final candle cannot satisfy the minimum history either.
    early = STRATEGY.evaluate(
        MARKET, candles, parameters, as_of=as_of - timedelta(microseconds=1)
    )
    assert early.intent == "hold"
    assert "have 24" in early.reason


@pytest.mark.parametrize("minutes", [5, 60, 1440])
def test_custom_parameters_and_intervals(minutes: int) -> None:
    candles = history("105", count=3, minutes=minutes)
    market = Market(id="eth", exchange="other", base="ETH", quote="USD")
    result = STRATEGY.evaluate(
        market,
        candles,
        {"lookback": 2, "entry_threshold_pct": "4", "exit_threshold_pct": 0},
        as_of=candles[-1].closed_at,
    )
    assert result.intent == "enter_long"
    assert "ETH/USD" in result.reason
    assert "over 2 candles" in result.reason
    assert "threshold 4%" in result.reason


@pytest.mark.parametrize(
    "parameters",
    [
        {"lookback": 0},
        {"lookback": -1},
        {"lookback": True},
        {"lookback": "24"},
        {"lookback": 2.5},
        {"lookback": None},
        {"entry_threshold_pct": 2.1},
        {"entry_threshold_pct": True},
        {"entry_threshold_pct": "NaN"},
        {"exit_threshold_pct": "Infinity"},
        {"exit_threshold_pct": "bad"},
        {"entry_threshold_pct": None},
        {"exit_threshold_pct": 2},
        {"exit_threshold_pct": 3},
        {"unknown": 1},
    ],
)
def test_invalid_parameters_fail_even_without_history(
    parameters: dict[str, JsonValue],
) -> None:
    with pytest.raises(ValidationError):
        STRATEGY.evaluate(MARKET, (), parameters, as_of=START)


@pytest.mark.parametrize(
    "kind", ["duplicate", "reversed", "overlap", "gap", "duration"]
)
def test_invalid_required_history_is_rejected(kind: str) -> None:
    candles = list(history())
    if kind == "duplicate":
        candles[-1] = candles[-2]
    elif kind == "reversed":
        candles[-2], candles[-1] = candles[-1], candles[-2]
    elif kind == "overlap":
        raw = candles[-1].model_dump()
        raw["opened_at"] -= timedelta(minutes=1)
        candles[-1] = Candle.model_validate(raw)
    elif kind == "gap":
        candles.pop(-2)
    else:
        raw = candles[-1].model_dump()
        raw["closed_at"] += timedelta(minutes=1)
        candles[-1] = Candle.model_validate(raw)
    with pytest.raises(ValueError):
        STRATEGY.evaluate(MARKET, tuple(candles), {}, as_of=START + timedelta(days=2))


def test_old_gaps_outside_required_window_are_irrelevant() -> None:
    candles = history(count=28)
    # Missing first candle's successor is outside the last 25-candle window.
    result = STRATEGY.evaluate(
        MARKET, (candles[0], *candles[3:]), {}, as_of=candles[-1].closed_at
    )
    assert result.intent == "enter_long"


@pytest.mark.parametrize(
    ("baseline", "price", "intent"),
    [
        ("3", "3.06", "hold"),  # Exact 2% with a non-power-of-ten baseline.
        ("100", "102.000000000000000000000000000001", "enter_long"),
        ("100", "98.999999999999999999999999999999", "exit_long"),
        ("1E-100", "1.03E-100", "enter_long"),
        ("1E100", "9.8E99", "exit_long"),
    ],
)
def test_threshold_comparisons_are_exact_and_context_independent(
    baseline: str, price: str, intent: str
) -> None:
    candles = history(price, baseline=baseline)
    with localcontext() as context:
        context.prec = 2
        context.traps[Inexact] = True
        result = STRATEGY.evaluate(MARKET, candles, {}, as_of=candles[-1].closed_at)
        assert context.prec == 2
    assert result.intent == intent


def test_naive_evaluation_time_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        STRATEGY.evaluate(MARKET, (), {}, as_of=datetime(2026, 1, 1))
