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


def test_runtime_and_migration_settings_are_separate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CROW_DATABASE_URL", "postgresql+psycopg://runtime@localhost/crow"
    )
    monkeypatch.delenv("CROW_MIGRATION_DATABASE_URL", raising=False)
    assert database_url().username == "runtime"
    with pytest.raises(PersistenceError, match="not configured"):
        database_url(migration=True)
