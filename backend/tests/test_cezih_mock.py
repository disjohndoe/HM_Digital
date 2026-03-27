import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cezih_status(client: AsyncClient, auth_headers: dict[str, str]):
    resp = await client.get("/api/cezih/status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["mock"] is True
    assert "connected" in data
    assert "mode" in data
    assert data["mode"] == "mock"


@pytest.mark.asyncio
async def test_cezih_status_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/cezih/status")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_insurance_check(client: AsyncClient, auth_headers: dict[str, str]):
    resp = await client.post(
        "/api/cezih/provjera-osiguranja",
        json={"mbo": "123456789"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mock"] is True
    assert data["mbo"] == "123456789"
    assert "ime" in data
    assert "prezime" in data
    assert "status_osiguranja" in data
    assert "osiguravatelj" in data


@pytest.mark.asyncio
async def test_insurance_check_unauthenticated(client: AsyncClient):
    resp = await client.post(
        "/api/cezih/provjera-osiguranja",
        json={"mbo": "123456789"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_e_uputnica_retrieve(client: AsyncClient, auth_headers: dict[str, str]):
    resp = await client.post("/api/cezih/e-uputnica/preuzmi", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["mock"] is True
    assert "items" in data
    assert len(data["items"]) > 0
    assert "id" in data["items"][0]
    assert "svrha" in data["items"][0]
    assert "status" in data["items"][0]


@pytest.mark.asyncio
async def test_e_uputnica_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/cezih/e-uputnica/preuzmi")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_e_recept_send(client: AsyncClient, auth_headers: dict[str, str], test_patient_id: str):
    resp = await client.post(
        "/api/cezih/e-recept",
        json={
            "patient_id": test_patient_id,
            "lijekovi": [{"naziv": "Amoksicilin 500mg", "doza": "500mg", "trajanje": "7 dana"}],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mock"] is True
    assert data["success"] is True
    assert "recept_id" in data


@pytest.mark.asyncio
async def test_e_recept_unauthenticated(client: AsyncClient):
    resp = await client.post(
        "/api/cezih/e-recept",
        json={"patient_id": "00000000-0000-0000-0000-000000000000", "lijekovi": []},
    )
    assert resp.status_code == 401
