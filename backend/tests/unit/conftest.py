"""Unit test conftest — override session-scoped DB fixtures from parent."""
import pytest


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Override parent conftest — no database needed for unit tests."""
    yield
