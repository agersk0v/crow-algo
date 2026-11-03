"""Safety-relevant validation of future execution and candle messages."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from crow_algo.domain import Candle, Fill, OrderIntent


def test_order_and_fill_preserve_exact_amounts_mode_and_configuration() -> None:
    order = OrderIntent(
        id="intent-1",
        strategy_instance_id="breakout",
        execution_account_id="paper",
        mode="paper",
        market_id="btc",
        configuration_version=2,
        side="buy",
        quantity="0.00000001",
        created_at="2026-01-01T01:00:00+01:00",
    )
    fill = Fill(
        id="fill-1",
        order_intent_id=order.id,
        execution_account_id="paper",
        mode="paper",
        quantity=order.quantity,
        price="12345.6789",
        fee="0.001",
        fee_currency="EUR",
        executed_at=order.created_at,
    )
    assert order.created_at == datetime(2026, 1, 1, tzinfo=UTC)
    assert OrderIntent.model_validate_json(order.model_dump_json()) == order
    assert Fill.model_validate_json(fill.model_dump_json()) == fill
    with pytest.raises(ValidationError):
        OrderIntent.model_validate({**order.model_dump(), "quantity": "0"})
    with pytest.raises(ValidationError):
        Fill.model_validate({**fill.model_dump(), "executed_at": "2026-01-01T00:00:00"})


@pytest.mark.parametrize(
    "changes",
    [
        {"closed_at": "2026-01-01T00:00:00Z"},
        {"high": "8"},
        {"low": "12"},
        {"close": "Infinity"},
        {"volume": "-1"},
    ],
)
def test_invalid_candle_data_is_rejected(changes: dict[str, str]) -> None:
    raw = {
        "opened_at": "2026-01-01T00:00:00Z",
        "closed_at": "2026-01-01T01:00:00Z",
        "open": "10",
        "high": "12",
        "low": "9",
        "close": "11",
        "volume": "100",
    }
    with pytest.raises(ValidationError):
        Candle.model_validate(raw | changes)
