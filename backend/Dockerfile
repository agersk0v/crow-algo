# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.12.23 AS uv
FROM python:3.12.14-slim-bookworm AS build
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1
COPY backend/ ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export SSL_CERT_FILE=/run/secrets/proxy_ca; fi; \
    uv sync --locked --no-dev --no-editable && chmod -R a+rX /app

FROM python:3.12.14-slim-bookworm AS runtime
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=build /app /app
USER 10001:10001
EXPOSE 8000
CMD ["sh", "-c", "python -m crow_algo.storage.migrate && exec uvicorn crow_algo.api.app:create_app --factory --host 0.0.0.0 --port 8000 --workers 1 --timeout-graceful-shutdown 10"]
