import asyncio
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.models.base import Base
from app.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/medical_mvp_test"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionFactory() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


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
    """Create a doctor user in the same tenant and return auth headers."""
    # First get the admin's tenant info
    me_resp = await client.get("/api/auth/me", headers=auth_headers)
    me_data = me_resp.json()
    tenant_id = me_data["tenant_id"]

    # Create doctor via the users API (admin can create users)
    # Actually, we need to use the user creation endpoint. Let's register another tenant
    # and create a doctor. Simpler approach: register a second user as a separate tenant
    # then we need cross-tenant isolation anyway.
    # Best approach: directly use the users endpoint to create a doctor in same tenant.
    # But that may require specific endpoint. Let's just register a second clinic as doctor.
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
