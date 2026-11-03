"""Invalid connection settings never expose their contents in diagnostics."""

import pytest

from crow_algo.database import PersistenceError, database_url


@pytest.mark.parametrize(
    "value", ["bad-url-with-secret", "sqlite:///secret", "postgresql://secret"]
)
def test_invalid_database_urls_have_safe_errors(value: str) -> None:
    with pytest.raises(PersistenceError) as result:
        database_url(value)
    assert value not in str(result.value)


def test_missing_database_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CROW_DATABASE_URL", raising=False)
    with pytest.raises(PersistenceError, match="not configured"):
        database_url()
