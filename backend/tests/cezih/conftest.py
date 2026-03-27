"""Override session fixtures for cezih unit tests — no database needed."""

import pytest


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """No-op override — cezih unit tests don't need a database."""
    yield
