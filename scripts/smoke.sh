#!/usr/bin/env bash
# Destructive smoke check ONLY for an explicitly named disposable test project.
set -euo pipefail

case "${CROW_COMPOSE_TEST_PROJECT:-}" in
  crow-test-*) ;;
  *) echo 'CROW_COMPOSE_TEST_PROJECT must start with crow-test-' >&2; exit 1 ;;
esac
cd "$(dirname "$0")/.."
compose=(docker compose -p "$CROW_COMPOSE_TEST_PROJECT")
base="http://127.0.0.1:${CROW_API_PORT:-8000}"
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT

probe() {
  local status
  status=$(curl --noproxy '*' --silent --max-time 12 \
    --output "$work_dir/response" --write-out '%{http_code}' "$base$1") || return 1
  [[ "$status" == "$2" ]] || return 1
  grep -q '"trading_enabled":false' "$work_dir/response"
}

wait_ready() {
  local deadline=$((SECONDS + 60))
  until probe /health/ready 200; do
    if (( SECONDS >= deadline )); then
      echo 'Backend did not become ready' >&2
      return 1
    fi
    sleep 0.5
  done
}

wait_ready
"${compose[@]}" exec -T backend python - <<'PY'
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
PY
"${compose[@]}" restart backend
wait_ready
"${compose[@]}" stop db
probe /health/live 200
probe /health/ready 503
"${compose[@]}" start db
wait_ready
"${compose[@]}" restart db
wait_ready
# Deliberately preserve the test volume and its saved record.
"${compose[@]}" down
"${compose[@]}" up -d --no-build --wait --wait-timeout 60
wait_ready
"${compose[@]}" exec -T backend python - <<'PY'
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
PY
"${compose[@]}" logs --no-color > "$work_dir/logs"
docker image inspect crow-algo-backend:local > "$work_dir/image"
docker history --no-trunc crow-algo-backend:local > "$work_dir/history"
password=${CROW_DB_PASSWORD:-$(sed -n 's/^CROW_DB_PASSWORD=//p' .env)}
if [[ -z "$password" ]]; then
  echo 'CROW_DB_PASSWORD must be set for the credential check' >&2
  exit 1
fi
printf '%s\n' "$password" > "$work_dir/password"
if grep -Fq -f "$work_dir/password" -- "$work_dir/logs" "$work_dir/image" "$work_dir/history"; then
  echo 'Credential found in logs or image metadata' >&2
  exit 1
fi
echo 'Compose restart, outage/recovery, and persistence checks passed.'
