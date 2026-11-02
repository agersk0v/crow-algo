"""Invalid connection settings never expose their contents in diagnostics."""

from pathlib import Path

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


def test_password_file_configuration_is_explicit_and_safe(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    password_file = tmp_path / "password"
    password_file.write_text("secret-marker\n")
    monkeypatch.setenv(
        "CROW_DATABASE_URL", "postgresql+psycopg://runtime@localhost/crow"
    )
    monkeypatch.setenv("CROW_DATABASE_PASSWORD_FILE", str(password_file))
    assert database_url().password == "secret-marker"
    # Explicit caller URLs must not inherit credentials from a different account.
    assert database_url("postgresql+psycopg://other@localhost/crow").password is None
    password_file.unlink()
    with pytest.raises(PersistenceError) as result:
        database_url()
    assert "secret-marker" not in str(result.value)
