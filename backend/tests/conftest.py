from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models.base import Base

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/medical_mvp_test"

_engine = None
_session_factory = None


async def _get_engine():
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _engine


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    engine = await _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(setup_database) -> AsyncGenerator[AsyncClient, None]:
    """Test client that uses the test database with per-request sessions."""

    async def override_get_db():
        async with _session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    # Disable rate limiting for tests
    app.state.limiter.enabled = False
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    app.state.limiter.enabled = True


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Direct DB session for tests that need to query/modify data directly."""
    async with _session_factory() as session:
        yield session


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    payload = {
        "naziv_klinike": "Test Ordinacija",
        "email": "admin@test.hr",
        "password": "Test1234!",
        "ime": "Test",
        "prezime": "Admin",
    }
    resp = await client.post("/api/auth/register", json=payload)
    data = resp.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def auth_headers_doctor(client: AsyncClient, auth_headers: dict[str, str]) -> dict[str, str]:
    """Create a doctor user in a separate tenant and return auth headers."""
    doctor_payload = {
        "naziv_klinike": "Doctor Clinic",
        "email": "doctor@test.hr",
        "password": "Test1234!",
        "ime": "Dr Test",
        "prezime": "Doctor",
    }
    resp = await client.post("/api/auth/register", json=doctor_payload)
    data = resp.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.fixture
async def test_patient_id(client: AsyncClient, auth_headers: dict[str, str]) -> str:
    payload = {
        "ime": "Ivan",
        "prezime": "Testić",
        "oib": "63789320451",
        "mbo": "123456789",
        "datum_rodjenja": "1990-01-15",
        "spol": "M",
        "telefon": "01/234-5678",
        "mobitel": "091/234-5678",
        "adresa": "Test ulica 1",
        "grad": "Zagreb",
        "postanski_broj": "10000",
    }
    resp = await client.post("/api/patients", json=payload, headers=auth_headers)
    return resp.json()["id"]
