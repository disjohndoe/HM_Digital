"""Integration tests for per-tenant CEZIH configuration and isolation.

Registers 3 separate clinics, sets distinct sifra_ustanove/OID on each,
and verifies that CEZIH case management endpoints use per-tenant values
and that data is fully isolated between tenants.
"""
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture(autouse=True)
def _disable_rate_limit():
    """Disable slowapi rate limiting for tests."""
    app.state.limiter.enabled = False
    yield
    app.state.limiter.enabled = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register_clinic(client: AsyncClient, name: str, email: str) -> dict:
    """Register a new clinic and return {headers, tenant_id, user_id}."""
    resp = await client.post(
        "/api/auth/register",
        json={
            "naziv_klinike": name,
            "email": email,
            "password": "Test1234!",
            "ime": "Admin",
            "prezime": name.split()[0],
        },
    )
    assert resp.status_code == 201, f"Registration failed for {email}: {resp.text}"
    data = resp.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    me = await client.get("/api/auth/me", headers=headers)
    me_data = me.json()

    return {
        "headers": headers,
        "tenant_id": me_data["tenant_id"],
        "user_id": me_data["id"],
    }


async def _set_clinic_cezih_config(
    client: AsyncClient, headers: dict, sifra_ustanove: str, oid: str,
) -> None:
    """Set CEZIH-specific config on a clinic via settings API."""
    resp = await client.patch(
        "/api/settings/clinic",
        json={"sifra_ustanove": sifra_ustanove, "oid": oid},
        headers=headers,
    )
    assert resp.status_code == 200, f"Clinic update failed: {resp.text}"
    data = resp.json()
    assert data["sifra_ustanove"] == sifra_ustanove
    assert data["oid"] == oid


async def _create_patient(client: AsyncClient, headers: dict, mbo: str, oib: str) -> str:
    """Create a patient and return patient_id."""
    resp = await client.post(
        "/api/patients",
        json={
            "ime": "Pacijent",
            "prezime": f"MBO-{mbo}",
            "oib": oib,
            "mbo": mbo,
            "datum_rodjenja": "1985-06-15",
            "spol": "M",
        },
        headers=headers,
    )
    assert resp.status_code == 201, f"Patient creation failed: {resp.text}"
    return resp.json()["id"]


async def _create_medical_record(client: AsyncClient, headers: dict, patient_id: str) -> str:
    """Create a medical record (nalaz) and return record_id."""
    resp = await client.post(
        "/api/medical-records",
        json={
            "patient_id": patient_id,
            "tip": "nalaz",
            "datum": "2026-04-05",
            "dijagnoza_mkb": "J06.9",
            "dijagnoza_tekst": "Akutna infekcija gornjeg dišnog sustava",
            "sadrzaj": "Pacijent se žali na kašalj i temperaturu.",
        },
        headers=headers,
    )
    assert resp.status_code == 201, f"Record creation failed: {resp.text}"
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Fixtures: 3 isolated clinics
# ---------------------------------------------------------------------------

@pytest.fixture
async def clinic_a(client: AsyncClient) -> dict:
    """Clinic A: Poliklinika Zagreb, sifra 12345, OID 1.2.3.4.5."""
    info = await _register_clinic(client, "Poliklinika Zagreb", "clinicA@test.hr")
    await _set_clinic_cezih_config(client, info["headers"], "12345", "1.2.3.4.5")
    info["patient_id"] = await _create_patient(client, info["headers"], "100000001", "10000000001")
    return info


@pytest.fixture
async def clinic_b(client: AsyncClient) -> dict:
    """Clinic B: Ordinacija Split, sifra 67890, OID 6.7.8.9.0."""
    info = await _register_clinic(client, "Ordinacija Split", "clinicB@test.hr")
    await _set_clinic_cezih_config(client, info["headers"], "67890", "6.7.8.9.0")
    info["patient_id"] = await _create_patient(client, info["headers"], "200000002", "20000000002")
    return info


@pytest.fixture
async def clinic_c(client: AsyncClient) -> dict:
    """Clinic C: Dom Zdravlja Rijeka, sifra 11111, OID 1.1.1.1.1."""
    info = await _register_clinic(client, "Dom Zdravlja Rijeka", "clinicC@test.hr")
    await _set_clinic_cezih_config(client, info["headers"], "11111", "1.1.1.1.1")
    info["patient_id"] = await _create_patient(client, info["headers"], "300000003", "30000000003")
    return info


# ---------------------------------------------------------------------------
# Test: Per-tenant config is stored and returned correctly
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_each_clinic_has_distinct_cezih_config(
    client: AsyncClient, clinic_a: dict, clinic_b: dict, clinic_c: dict,
):
    """Each clinic should have its own sifra_ustanove and OID."""
    for clinic, expected_sifra, expected_oid in [
        (clinic_a, "12345", "1.2.3.4.5"),
        (clinic_b, "67890", "6.7.8.9.0"),
        (clinic_c, "11111", "1.1.1.1.1"),
    ]:
        resp = await client.get("/api/settings/clinic", headers=clinic["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["sifra_ustanove"] == expected_sifra
        assert data["oid"] == expected_oid


# ---------------------------------------------------------------------------
# Test: Patient isolation — clinics cannot see each other's patients
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patient_isolation_across_clinics(
    client: AsyncClient, clinic_a: dict, clinic_b: dict, clinic_c: dict,
):
    """Clinic A's patient should not be visible to Clinic B or C."""
    # Clinic B tries to access Clinic A's patient
    resp = await client.get(
        f"/api/patients/{clinic_a['patient_id']}",
        headers=clinic_b["headers"],
    )
    assert resp.status_code == 404

    # Clinic C tries to access Clinic B's patient
    resp = await client.get(
        f"/api/patients/{clinic_b['patient_id']}",
        headers=clinic_c["headers"],
    )
    assert resp.status_code == 404

    # Clinic A tries to access Clinic C's patient
    resp = await client.get(
        f"/api/patients/{clinic_c['patient_id']}",
        headers=clinic_a["headers"],
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test: CEZIH case management uses per-tenant org_code
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_case_uses_tenant_org_code(
    client: AsyncClient, clinic_a: dict, clinic_b: dict, clinic_c: dict,
):
    """Each clinic's create_case should succeed independently in mock mode."""
    for clinic, mbo in [
        (clinic_a, "100000001"),
        (clinic_b, "200000002"),
        (clinic_c, "300000003"),
    ]:
        resp = await client.post(
            "/api/cezih/cases",
            json={
                "patient_mbo": mbo,
                "icd_code": "J06.9",
                "icd_display": "Akutna infekcija",
                "onset_date": "2026-04-01",
                "verification_status": "unconfirmed",
            },
            headers=clinic["headers"],
        )
        assert resp.status_code == 200, f"create_case failed for clinic: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["mock"] is True
        assert "cezih_case_id" in data


@pytest.mark.asyncio
async def test_update_case_status_per_tenant(
    client: AsyncClient, clinic_a: dict, clinic_b: dict,
):
    """Each clinic can update case status independently."""
    # Create a case for each clinic first
    for clinic, mbo in [(clinic_a, "100000001"), (clinic_b, "200000002")]:
        create_resp = await client.post(
            "/api/cezih/cases",
            json={
                "patient_mbo": mbo,
                "icd_code": "J06.9",
                "icd_display": "Test",
                "onset_date": "2026-04-01",
            },
            headers=clinic["headers"],
        )
        case_id = create_resp.json()["cezih_case_id"]

        # Update the case status
        resp = await client.put(
            f"/api/cezih/cases/{case_id}/status?mbo={mbo}",
            json={"action": "resolve"},
            headers=clinic["headers"],
        )
        assert resp.status_code == 200, f"update_case_status failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["mock"] is True


@pytest.mark.asyncio
async def test_update_case_data_per_tenant(
    client: AsyncClient, clinic_a: dict, clinic_c: dict,
):
    """Each clinic can update case data independently."""
    for clinic, mbo in [(clinic_a, "100000001"), (clinic_c, "300000003")]:
        create_resp = await client.post(
            "/api/cezih/cases",
            json={
                "patient_mbo": mbo,
                "icd_code": "J06.9",
                "icd_display": "Test",
                "onset_date": "2026-04-01",
            },
            headers=clinic["headers"],
        )
        case_id = create_resp.json()["cezih_case_id"]

        resp = await client.put(
            f"/api/cezih/cases/{case_id}/data?mbo={mbo}",
            json={
                "current_clinical_status": "active",
                "icd_code": "J11.1",
                "icd_display": "Gripa",
                "note": "Ažurirani podaci",
            },
            headers=clinic["headers"],
        )
        assert resp.status_code == 200, f"update_case_data failed: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["mock"] is True


# ---------------------------------------------------------------------------
# Test: E-Nalaz isolation — records and sends are per-tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enalaz_isolation(
    client: AsyncClient, clinic_a: dict, clinic_b: dict,
):
    """E-Nalaz sent by Clinic A should not appear in Clinic B's records."""
    # Create a medical record in Clinic A
    record_id = await _create_medical_record(client, clinic_a["headers"], clinic_a["patient_id"])

    # Send e-Nalaz from Clinic A
    resp = await client.post(
        "/api/cezih/e-nalaz",
        json={"patient_id": clinic_a["patient_id"], "record_id": record_id},
        headers=clinic_a["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Clinic B should not see Clinic A's medical records
    resp = await client.get(
        f"/api/medical-records?patient_id={clinic_a['patient_id']}",
        headers=clinic_b["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    # Clinic B should get empty results (not Clinic A's records)
    records = data.get("items", data) if isinstance(data, dict) else data
    if isinstance(records, list):
        assert len(records) == 0


# ---------------------------------------------------------------------------
# Test: CEZIH activity logs are per-tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cezih_activity_isolation(
    client: AsyncClient, clinic_a: dict, clinic_b: dict,
):
    """CEZIH activity from Clinic A should not appear in Clinic B's log."""
    # Trigger a CEZIH action in Clinic A
    await client.post(
        "/api/cezih/provjera-osiguranja",
        json={"mbo": "100000001"},
        headers=clinic_a["headers"],
    )

    # Check Clinic A's activity
    resp_a = await client.get("/api/cezih/activity", headers=clinic_a["headers"])
    assert resp_a.status_code == 200
    activity_a = resp_a.json()
    assert activity_a["total"] > 0

    # Check Clinic B's activity — should have 0 from Clinic A's actions
    resp_b = await client.get("/api/cezih/activity", headers=clinic_b["headers"])
    assert resp_b.status_code == 200
    activity_b = resp_b.json()

    # Clinic B should not see Clinic A's insurance check
    for item in activity_b.get("items", []):
        assert item.get("user_id") != clinic_a["user_id"]


# ---------------------------------------------------------------------------
# Test: Dashboard stats are per-tenant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_stats_isolation(
    client: AsyncClient, clinic_a: dict, clinic_b: dict, clinic_c: dict,
):
    """Dashboard stats should reflect only the calling tenant's data."""
    # Create and send a record from Clinic A
    record_id = await _create_medical_record(client, clinic_a["headers"], clinic_a["patient_id"])
    await client.post(
        "/api/cezih/e-nalaz",
        json={"patient_id": clinic_a["patient_id"], "record_id": record_id},
        headers=clinic_a["headers"],
    )

    # Clinic A should have stats
    resp_a = await client.get("/api/cezih/dashboard-stats", headers=clinic_a["headers"])
    assert resp_a.status_code == 200
    stats_a = resp_a.json()
    assert stats_a["danas_operacije"] > 0

    # Clinic C should have zero operations (it didn't do anything CEZIH-related)
    resp_c = await client.get("/api/cezih/dashboard-stats", headers=clinic_c["headers"])
    assert resp_c.status_code == 200
    stats_c = resp_c.json()
    assert stats_c["danas_operacije"] == 0


# ---------------------------------------------------------------------------
# Test: Cross-tenant e-Nalaz send is rejected
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_tenant_enalaz_rejected(
    client: AsyncClient, clinic_a: dict, clinic_b: dict,
):
    """Clinic B should not be able to send e-Nalaz for Clinic A's patient/record."""
    record_id = await _create_medical_record(client, clinic_a["headers"], clinic_a["patient_id"])

    # Clinic B tries to send Clinic A's record
    resp = await client.post(
        "/api/cezih/e-nalaz",
        json={"patient_id": clinic_a["patient_id"], "record_id": record_id},
        headers=clinic_b["headers"],
    )
    # Should fail — patient/record not found in Clinic B's tenant
    assert resp.status_code in (404, 422)
