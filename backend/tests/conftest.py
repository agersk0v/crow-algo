"""Explicit opt-in for tests that create disposable PostgreSQL resources."""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--require-postgres",
        action="store_true",
        help="fail rather than skip if CROW_TEST_ADMIN_URL is missing",
    )
