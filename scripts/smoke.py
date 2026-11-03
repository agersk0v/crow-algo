"""Destructive smoke check ONLY for an explicitly named disposable test project."""

import os
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, build_opener


def main() -> None:
    project = os.environ.get("CROW_COMPOSE_TEST_PROJECT", "")
    if not project.startswith("crow-test-"):
        raise SystemExit("CROW_COMPOSE_TEST_PROJECT must start with crow-test-")
    compose = ["docker", "compose", "-p", project]
    opener = build_opener(ProxyHandler({}))  # Localhost health checks only.
    base = "http://127.0.0.1:" + os.environ.get("CROW_API_PORT", "8000")

    def run(*args: str) -> None:
        subprocess.run([*compose, *args], check=True, timeout=90)

    def probe(endpoint: str) -> int:
        try:
            with opener.open(base + endpoint, timeout=12) as response:
                assert b'"trading_enabled":false' in response.read()
                return int(response.status)
        except HTTPError as exc:
            return exc.code
        except (URLError, TimeoutError, ConnectionError):
            return 0

    def wait_ready() -> None:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if probe("/health/ready") == 200:
                return
            time.sleep(0.5)
        raise RuntimeError("backend did not become ready")

    def backend(code: str) -> None:
        run("exec", "-T", "backend", "python", "-c", code)

    wait_ready()
    backend("""
from sqlalchemy import text
from crow_algo.storage.database import database_engine, save_configuration
from crow_algo.config import Configuration
config = Configuration.model_validate({
    'version': 1,
    'markets': [{'id': 'btc', 'exchange': 'kraken', 'base': 'BTC', 'quote': 'EUR'}],
    'execution_accounts': [{'id': 'paper', 'exchange': 'kraken', 'mode': 'paper',
                            'quote_currency': 'EUR', 'budget': '0'}],
    'allocation_accounts': [
        {'id': 'one', 'execution_account_id': 'paper', 'budget': '0'}],
    'strategies': [{'id': 'one', 'strategy_type': 'momentum', 'strategy_version': 1,
                    'market_ids': ['btc'], 'timeframe': '1h',
                    'allocation_account_id': 'one'}],
})
engine = database_engine()
try:
    with engine.begin() as connection:
        query = text('SELECT count(*) FROM configuration_versions')
        assert connection.execute(query).scalar_one() == 0
        save_configuration(connection, config)
finally:
    engine.dispose()
""")
    run("restart", "backend")
    wait_ready()
    run("stop", "db")
    assert probe("/health/live") == 200
    assert probe("/health/ready") == 503
    run("start", "db")
    wait_ready()
    run("restart", "db")
    wait_ready()
    run("down")  # Deliberately preserve the test volume and its saved record.
    run("up", "-d", "--no-build", "--wait", "--wait-timeout", "60")
    wait_ready()
    backend("""
from sqlalchemy import text
from crow_algo.storage.database import database_engine, load_configuration
from pathlib import Path
import os
assert not Path('/app/.env').exists()
assert not any(key.startswith('CROW_MIGRATION_') for key in os.environ)
engine = database_engine()
try:
    with engine.connect() as connection:
        assert load_configuration(connection, 1).execution_accounts[0].budget == 0
        assert connection.execute(text(
            'SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles '
            'WHERE rolname=current_user'
        )).one() == (False, False, False)
        assert set(connection.execute(text(
            'SELECT rolname FROM pg_roles WHERE rolcanlogin'
        )).scalars()) == {'crow_algo'}
        query = text('SELECT count(*) FROM configuration_versions')
        assert connection.execute(query).scalar_one() == 1
        assert set(connection.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname='public'"
        )).scalars()) == {'alembic_version', 'configuration_versions'}
finally:
    engine.dispose()
""")
    logs = subprocess.check_output([*compose, "logs", "--no-color"], timeout=30)
    image = subprocess.check_output(
        ["docker", "image", "inspect", "crow-algo-backend:local"], timeout=30
    )
    history = subprocess.check_output(
        ["docker", "history", "--no-trunc", "crow-algo-backend:local"], timeout=30
    )
    values = dict(
        line.split("=", 1)
        for line in Path(".env").read_text().splitlines()
        if line and not line.startswith("#")
    )
    password = os.environ.get("CROW_DB_PASSWORD", values["CROW_DB_PASSWORD"]).encode()
    if password and any(password in output for output in (logs, image, history)):
        raise RuntimeError("credential found in logs or image metadata")
    print("Compose restart, outage/recovery, and persistence checks passed.")


if __name__ == "__main__":
    main()
