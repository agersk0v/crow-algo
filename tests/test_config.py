"""Configuration rejection and eligibility without network or trading activity."""

from copy import deepcopy
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from crow_algo.config import Configuration, UnsupportedActivation, validate_activation


def configuration() -> dict[str, Any]:
    # These amounts and parameters are test data, not proposed trading settings.
    return {
        "version": 1,
        "markets": [{"id": "btc", "exchange": "kraken", "base": "BTC", "quote": "EUR"}],
        "execution_accounts": [
            {
                "id": "paper",
                "exchange": "kraken",
                "mode": "paper",
                "quote_currency": "EUR",
                "budget": "200.10",
            }
        ],
        "allocation_accounts": [
            {"id": "allocation", "execution_account_id": "paper", "budget": "100.05"}
        ],
        "strategies": [
            {
                "id": "breakout",
                "strategy_type": "momentum",
                "strategy_version": 1,
                "parameters": {},
                "market_ids": ["btc"],
                "timeframe": "1h",
                "allocation_account_id": "allocation",
            }
        ],
    }


@pytest.mark.parametrize(
    "collection", ["markets", "execution_accounts", "allocation_accounts", "strategies"]
)
def test_duplicate_ids_are_rejected(collection: str) -> None:
    raw = configuration()
    raw[collection].append(deepcopy(raw[collection][0]))
    with pytest.raises(ValidationError, match="duplicate IDs"):
        Configuration.model_validate(raw)


@pytest.mark.parametrize(
    "value", ["-1", "NaN", "Infinity", "-Infinity", "bad", True, 1.1]
)
@pytest.mark.parametrize("collection", ["execution_accounts", "allocation_accounts"])
def test_invalid_amounts_are_rejected(collection: str, value: object) -> None:
    raw = configuration()
    raw[collection][0]["budget"] = value
    with pytest.raises(ValidationError):
        Configuration.model_validate(raw)


@pytest.mark.parametrize(
    ("collection", "field", "value", "message"),
    [
        ("allocation_accounts", "execution_account_id", "missing", "unknown execution"),
        ("strategies", "allocation_account_id", "missing", "unknown allocation"),
        ("strategies", "market_ids", ["missing"], "unknown market"),
        ("strategies", "market_ids", ["btc", "btc"], "duplicate market references"),
        ("markets", "exchange", "other", "does not match"),
        ("markets", "quote", "USD", "does not match"),
    ],
)
def test_invalid_references_are_rejected(
    collection: str, field: str, value: object, message: str
) -> None:
    raw = configuration()
    raw[collection][0][field] = value
    with pytest.raises(ValidationError, match=message):
        Configuration.model_validate(raw)


def test_allocation_totals_are_exact_and_cannot_double_spend() -> None:
    raw = configuration()
    raw["execution_accounts"][0]["budget"] = "10000000000000000000000000000"
    raw["allocation_accounts"][0]["budget"] = "9999999999999999999999999999.99"
    raw["allocation_accounts"].append(
        {"id": "extra", "execution_account_id": "paper", "budget": "0.02"}
    )
    with pytest.raises(ValidationError, match="allocations exceed"):
        Configuration.model_validate(raw)
    raw["allocation_accounts"][1]["budget"] = "0.01"
    Configuration.model_validate(raw)


def test_strategy_allocation_cannot_be_shared() -> None:
    raw = configuration()
    raw["strategies"].append({**raw["strategies"][0], "id": "second"})
    with pytest.raises(ValidationError, match="separate allocation"):
        Configuration.model_validate(raw)


@pytest.mark.parametrize(
    ("base", "quote", "interval", "amount"),
    [
        ("BTC", "EUR", "1h", "200.10"),
        ("ETH", "USD", "5m", "98765.4321"),
        ("SOL", "USDT", "1d", "0.01"),
    ],
)
def test_configuration_is_not_tied_to_pair_interval_or_budget(
    base: str, quote: str, interval: str, amount: str
) -> None:
    raw = configuration()
    raw["markets"][0].update(base=base, quote=quote)
    raw["execution_accounts"][0].update(quote_currency=quote, budget=amount)
    raw["allocation_accounts"][0]["budget"] = amount
    raw["strategies"][0]["timeframe"] = interval
    config = Configuration.model_validate(raw)
    restored = Configuration.model_validate_json(config.model_dump_json())
    assert restored == config
    assert restored.execution_accounts[0].budget == Decimal(amount)
    assert restored.markets[0].symbol == f"{base}/{quote}"
    assert validate_activation(config, ["breakout"]).id == "breakout"


@pytest.mark.parametrize("interval", ["0h", "-1h", "1hour", "", "1.5h"])
def test_invalid_timeframes_are_rejected(interval: str) -> None:
    raw = configuration()
    raw["strategies"][0]["timeframe"] = interval
    with pytest.raises(ValidationError):
        Configuration.model_validate(raw)


def test_future_configuration_is_describable_but_not_activatable() -> None:
    raw = configuration()
    raw["markets"].append(
        {"id": "eth", "exchange": "kraken", "base": "ETH", "quote": "EUR"}
    )
    raw["allocation_accounts"].append(
        {"id": "second-allocation", "execution_account_id": "paper", "budget": "100.05"}
    )
    raw["strategies"].append(
        {
            **raw["strategies"][0],
            "id": "second",
            "market_ids": ["eth"],
            "allocation_account_id": "second-allocation",
        }
    )
    config = Configuration.model_validate(raw)
    assert validate_activation(config, ["second"]).id == "second"
    with pytest.raises(UnsupportedActivation, match="exactly one strategy"):
        validate_activation(config, ["breakout", "second"])
    raw["strategies"][0]["market_ids"] = ["btc", "eth"]
    with pytest.raises(UnsupportedActivation, match="exactly one market"):
        validate_activation(Configuration.model_validate(raw), ["breakout"])


@pytest.mark.parametrize("selected", [[], ["missing"], ["breakout", "breakout"]])
def test_invalid_activation_selection_is_rejected(selected: list[str]) -> None:
    with pytest.raises(UnsupportedActivation):
        validate_activation(Configuration.model_validate(configuration()), selected)


def test_live_configuration_never_grants_live_activation() -> None:
    raw = configuration()
    raw["execution_accounts"][0]["mode"] = "live"
    config = Configuration.model_validate(raw)
    assert config.execution_accounts[0].mode == "live"
    with pytest.raises(UnsupportedActivation, match="live activation"):
        validate_activation(config, ["breakout"])


def test_unknown_strategy_is_declarative_only() -> None:
    raw = configuration()
    raw["strategies"][0]["strategy_type"] = "future-strategy"
    with pytest.raises(UnsupportedActivation, match="momentum version 1"):
        validate_activation(Configuration.model_validate(raw), ["breakout"])


def test_typos_and_nonfinite_parameters_are_rejected() -> None:
    raw = configuration()
    raw["strategies"][0]["parameters"] = {"threshold": float("nan")}
    with pytest.raises(ValidationError):
        Configuration.model_validate(raw)
    raw = configuration()
    raw["strategies"][0]["timefame"] = "1d"
    with pytest.raises(ValidationError, match="Extra inputs"):
        Configuration.model_validate(raw)
