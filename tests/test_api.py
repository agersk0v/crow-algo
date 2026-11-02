"""Health responses remain safe and live during a blocking database probe."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from crow_algo.api import create_app
from crow_algo.database import database_engine


def test_liveness_remains_responsive_during_readiness_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = database_engine("postgresql+psycopg://user:secret-marker@unused/crow")
    entered, release = Event(), Event()

    def blocked_connection() -> None:
        entered.set()
        assert release.wait(5)
        raise OperationalError("secret-marker", None, RuntimeError("secret-marker"))

    monkeypatch.setattr(engine, "connect", blocked_connection)
    try:
        with TestClient(create_app(engine)) as client, ThreadPoolExecutor() as executor:
            pending = executor.submit(client.get, "/health/ready")
            try:
                assert entered.wait(5)
                response = client.get("/health/live")
                assert response.status_code == 200
                assert response.json() == {"status": "alive", "trading_enabled": False}
            finally:
                release.set()
            failed = pending.result(timeout=5)
            assert failed.status_code == 503
            assert failed.json() == {"status": "unavailable", "trading_enabled": False}
            assert "secret-marker" not in failed.text
    finally:
        engine.dispose()


def test_application_disposes_its_owned_pool_without_connecting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = database_engine("postgresql+psycopg://user@unused/crow")
    disposed: list[bool] = []
    monkeypatch.setattr("crow_algo.api.database_engine", lambda: engine)
    monkeypatch.setattr(engine, "dispose", lambda: disposed.append(True))
    with TestClient(create_app()) as client:
        assert client.get("/health/live").status_code == 200
        assert not disposed
    assert disposed == [True]
