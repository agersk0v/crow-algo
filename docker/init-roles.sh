#!/bin/sh
set -eu

# Only executed by the official image when initializing a new database volume.
# Passwords stay in mounted files/psql memory, not command-line arguments or logs.
psql --no-psqlrc --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    --set ON_ERROR_STOP=1 <<'SQL'
SET log_min_error_statement TO panic;
SET log_statement TO none;
\set migration_password `cat /run/secrets/migration_password`
\set runtime_password `cat /run/secrets/runtime_password`
CREATE ROLE crow_migrate LOGIN PASSWORD :'migration_password';
CREATE ROLE crow_runtime LOGIN PASSWORD :'runtime_password';
ALTER DATABASE crow_algo OWNER TO crow_migrate;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
SQL
