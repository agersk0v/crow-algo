-- One application login owns the schema; PostgreSQL's bootstrap login is disabled.
\getenv app_password POSTGRES_PASSWORD
CREATE ROLE crow_algo LOGIN PASSWORD :'app_password';
ALTER DATABASE crow_algo OWNER TO crow_algo;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
ALTER ROLE postgres NOLOGIN;
