import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.cezih_euputnica import CezihEUputnica
from app.models.medical_record import MedicalRecord


_MOCK_NAMES = [
    ("Ivan", "Horvat", "1985-03-15"),
    ("Ana", "Kovačević", "1990-07-22"),
    ("Marko", "Marić", "1978-11-08"),
    ("Petra", "Jurić", "1995-01-30"),
    ("Luka", "Novak", "1982-09-12"),
]

_MOCK_OSIGURAVATELJI = ["HZZO", "HZZO", "HZZO", "Adria Osiguranje", "CROATIA osiguranje"]
_MOCK_STATUS = ["Aktivan", "Aktivan", "Aktivan", "Aktivan", "Na čekanju"]


def _deterministic_index(mbo: str) -> int:
    return int(hashlib.md5(mbo.encode()).hexdigest(), 16) % len(_MOCK_NAMES)


async def _write_audit(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    action: str,
    resource_id: UUID | None = None,
    details: dict | None = None,
) -> None:
    entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type="cezih",
        resource_id=resource_id,
        details=json.dumps(details, default=str) if details else None,
    )
    db.add(entry)
    await db.flush()


async def mock_insurance_check(
    mbo: str,
    db: AsyncSession | None = None,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
) -> dict:
    idx = _deterministic_index(mbo)
    name = _MOCK_NAMES[idx]

    result = {
        "mock": True,
        "mbo": mbo,
        "ime": name[0],
        "prezime": name[1],
        "datum_rodjenja": name[2],
        "osiguravatelj": _MOCK_OSIGURAVATELJI[idx],
        "status_osiguranja": _MOCK_STATUS[idx],
        "broj_osiguranja": f"HR-{mbo[-6:]}",
    }

    if db and user_id and tenant_id:
        await _write_audit(
            db, tenant_id, user_id,
            action="insurance_check",
            details={"mbo": mbo, "result": result["status_osiguranja"]},
        )

    return result


async def mock_send_enalaz(
    db: AsyncSession,
    tenant_id: UUID,
    patient_id: UUID,
    record_id: UUID,
    user_id: UUID | None = None,
    uputnica_id: str | None = None,
) -> dict:
    import os

    ref = f"MOCK-EN-{os.urandom(4).hex()}"
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.id == record_id,
            MedicalRecord.tenant_id == tenant_id,
            MedicalRecord.patient_id == patient_id,
        )
    )
    record = result.scalar_one_or_none()
    if record:
        record.cezih_sent = True
        record.cezih_sent_at = now
        record.cezih_reference_id = ref
        await db.flush()

    # Close the linked referral in the DB if provided
    if uputnica_id:
        uputnica_result = await db.execute(
            select(CezihEUputnica).where(
                CezihEUputnica.tenant_id == tenant_id,
                CezihEUputnica.external_id == uputnica_id,
            )
        )
        uputnica_row = uputnica_result.scalar_one_or_none()
        if uputnica_row:
            uputnica_row.status = "Zatvorena"
            await db.flush()

    details: dict = {
        "patient_id": str(patient_id),
        "record_id": str(record_id),
        "reference_id": ref,
    }
    if uputnica_id:
        details["uputnica_id"] = uputnica_id

    if user_id:
        await _write_audit(
            db, tenant_id, user_id,
            action="e_nalaz_send",
            resource_id=patient_id,
            details=details,
        )

    return {
        "mock": True,
        "success": True,
        "reference_id": ref,
        "sent_at": now.isoformat(),
    }


_MOCK_EUPUTNICE = [
    {
        "external_id": "EU-2026-001",
        "datum_izdavanja": "2026-03-15",
        "izdavatelj": "DOM ZDRAVLJA ZAGREB-CENTAR",
        "svrha": "Kardiološki pregled",
        "specijalist": "Dr. sc. med. Josip Babić, dr. med.",
        "status": "Otvorena",
    },
    {
        "external_id": "EU-2026-002",
        "datum_izdavanja": "2026-03-10",
        "izdavatelj": "DOM ZDRAVLJA SPLIT",
        "svrha": "Dermatološka pretraga",
        "specijalist": "Prof. dr. sc. Marija Perić",
        "status": "Zatvorena",
    },
    {
        "external_id": "EU-2026-003",
        "datum_izdavanja": "2026-03-20",
        "izdavatelj": "POLIKLINIKA RIJEKA",
        "svrha": "Ortopedska konzultacija",
        "specijalist": "Dr. Ante Tomić, dr. med.",
        "status": "Otvorena",
    },
    {
        "external_id": "EU-2026-004",
        "datum_izdavanja": "2026-03-24",
        "izdavatelj": "KBC ZAGREB",
        "svrha": "Neurološki pregled",
        "specijalist": "Dr. sc. Ivan Matić, dr. med.",
        "status": "Otvorena",
    },
    {
        "external_id": "EU-2026-005",
        "datum_izdavanja": "2026-03-25",
        "izdavatelj": "DOM ZDRAVLJA OSIJEK",
        "svrha": "Oftalmološki pregled",
        "specijalist": "Dr. Lana Herceg, dr. med.",
        "status": "Otvorena",
    },
]


async def mock_retrieve_euputnice(
    db: AsyncSession | None = None,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
) -> dict:
    """Fetch new e-Uputnice from CEZIH (mock) and persist them.

    Existing referrals are updated; new ones are inserted.
    Returns only the newly fetched batch (for the toast count).
    """
    new_count = 0

    if db and tenant_id:
        # Determine which referrals should be closed (e-Nalaz linked)
        nalaz_result = await db.execute(
            select(AuditLog.details).where(
                AuditLog.tenant_id == tenant_id,
                AuditLog.resource_type == "cezih",
                AuditLog.action == "e_nalaz_send",
            )
        )
        closed_ids: set[str] = set()
        for (details_str,) in nalaz_result.all():
            if details_str:
                details = json.loads(details_str)
                uid = details.get("uputnica_id")
                if uid:
                    closed_ids.add(uid)

        # Upsert each mock referral into the DB
        for item in _MOCK_EUPUTNICE:
            ext_id = item["external_id"]
            status = "Zatvorena" if ext_id in closed_ids or item["status"] == "Zatvorena" else "Otvorena"

            existing = await db.execute(
                select(CezihEUputnica).where(
                    CezihEUputnica.tenant_id == tenant_id,
                    CezihEUputnica.external_id == ext_id,
                )
            )
            row = existing.scalar_one_or_none()
            if row:
                # Update status if changed
                row.status = status
            else:
                db.add(CezihEUputnica(
                    tenant_id=tenant_id,
                    external_id=ext_id,
                    datum_izdavanja=item["datum_izdavanja"],
                    izdavatelj=item["izdavatelj"],
                    svrha=item["svrha"],
                    specijalist=item["specijalist"],
                    status=status,
                ))
                new_count += 1

        await db.flush()

    if db and user_id and tenant_id:
        await _write_audit(
            db, tenant_id, user_id,
            action="e_uputnica_retrieve",
            details={"count": len(_MOCK_EUPUTNICE), "new": new_count},
        )

    # Return the full persisted list
    return await get_stored_euputnice(db, tenant_id)


async def get_stored_euputnice(
    db: AsyncSession | None,
    tenant_id: UUID | None,
) -> dict:
    """Read all persisted e-Uputnice for the tenant."""
    if not db or not tenant_id:
        return {"mock": True, "items": []}

    result = await db.execute(
        select(CezihEUputnica)
        .where(CezihEUputnica.tenant_id == tenant_id)
        .order_by(CezihEUputnica.datum_izdavanja.desc())
    )
    rows = result.scalars().all()

    items = [
        {
            "mock": True,
            "id": r.external_id,
            "datum_izdavanja": r.datum_izdavanja,
            "izdavatelj": r.izdavatelj,
            "svrha": r.svrha,
            "specijalist": r.specijalist,
            "status": r.status,
        }
        for r in rows
    ]
    return {"mock": True, "items": items}


async def mock_send_erecept(
    patient_id: UUID,
    lijekovi: list[dict],
    db: AsyncSession | None = None,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
) -> dict:
    import os

    recept_id = f"MOCK-ER-{os.urandom(4).hex()}"

    if db and user_id and tenant_id:
        await _write_audit(
            db, tenant_id, user_id,
            action="e_recept_send",
            resource_id=patient_id,
            details={
                "patient_id": str(patient_id),
                "recept_id": recept_id,
                "lijekovi": [l.get("naziv", "") if isinstance(l, dict) else str(l) for l in lijekovi],
            },
        )

    return {
        "mock": True,
        "success": True,
        "recept_id": recept_id,
    }


def mock_cezih_status(tenant_id=None) -> dict:
    from app.services.agent_connection_manager import agent_manager

    agent_connected = False
    last_heartbeat = None
    if tenant_id:
        agent_connected = agent_manager.is_connected(tenant_id)
        conn = agent_manager.get(tenant_id)
        if conn:
            last_heartbeat = conn.last_heartbeat

    return {
        "mock": True,
        "connected": False,
        "mode": "mock",
        "agent_connected": agent_connected,
        "last_heartbeat": last_heartbeat,
    }


# --- Feature 4: Mock Drug List ---

MOCK_LIJEKOVI = [
    {"atk": "N02BE01", "naziv": "Paracetamol 500mg", "oblik": "tableta", "jacina": "500 mg"},
    {"atk": "N02BA01", "naziv": "Aspirin 500mg", "oblik": "tableta", "jacina": "500 mg"},
    {"atk": "M01AE01", "naziv": "Ibuprofen 400mg", "oblik": "tableta", "jacina": "400 mg"},
    {"atk": "M01AE01", "naziv": "Ibuprofen 600mg", "oblik": "tableta", "jacina": "600 mg"},
    {"atk": "N02AX02", "naziv": "Tramadol 50mg", "oblik": "kapsula", "jacina": "50 mg"},
    {"atk": "C07AB02", "naziv": "Metoprolol 50mg", "oblik": "tableta", "jacina": "50 mg"},
    {"atk": "C09AA02", "naziv": "Enalapril 10mg", "oblik": "tableta", "jacina": "10 mg"},
    {"atk": "C09AA05", "naziv": "Ramipril 5mg", "oblik": "tableta", "jacina": "5 mg"},
    {"atk": "C10AA05", "naziv": "Atorvastatin 20mg", "oblik": "tableta", "jacina": "20 mg"},
    {"atk": "C10AA01", "naziv": "Simvastatin 20mg", "oblik": "tableta", "jacina": "20 mg"},
    {"atk": "A02BC01", "naziv": "Omeprazol 20mg", "oblik": "kapsula", "jacina": "20 mg"},
    {"atk": "A02BC02", "naziv": "Pantoprazol 40mg", "oblik": "tableta", "jacina": "40 mg"},
    {"atk": "J01CA04", "naziv": "Amoksicilin 500mg", "oblik": "kapsula", "jacina": "500 mg"},
    {"atk": "J01CR02", "naziv": "Amoksicilin + klavulanska kiselina 1g", "oblik": "tableta", "jacina": "875/125 mg"},
    {"atk": "J01FA10", "naziv": "Azitromicin 500mg", "oblik": "tableta", "jacina": "500 mg"},
    {"atk": "J01MA02", "naziv": "Ciprofloksacin 500mg", "oblik": "tableta", "jacina": "500 mg"},
    {"atk": "A10BA02", "naziv": "Metformin 850mg", "oblik": "tableta", "jacina": "850 mg"},
    {"atk": "A10BA02", "naziv": "Metformin 1000mg", "oblik": "tableta", "jacina": "1000 mg"},
    {"atk": "C03CA01", "naziv": "Furosemid 40mg", "oblik": "tableta", "jacina": "40 mg"},
    {"atk": "B01AC06", "naziv": "Acetilsalicilna kiselina 100mg", "oblik": "tableta", "jacina": "100 mg"},
    {"atk": "N05BA01", "naziv": "Diazepam 5mg", "oblik": "tableta", "jacina": "5 mg"},
    {"atk": "N06AB06", "naziv": "Sertralin 50mg", "oblik": "tableta", "jacina": "50 mg"},
    {"atk": "N06AB04", "naziv": "Citalopram 20mg", "oblik": "tableta", "jacina": "20 mg"},
    {"atk": "R06AE07", "naziv": "Cetirizin 10mg", "oblik": "tableta", "jacina": "10 mg"},
    {"atk": "R06AX13", "naziv": "Loratadin 10mg", "oblik": "tableta", "jacina": "10 mg"},
    {"atk": "H02AB06", "naziv": "Prednizon 5mg", "oblik": "tableta", "jacina": "5 mg"},
    {"atk": "H02AB04", "naziv": "Metilprednizolon 4mg", "oblik": "tableta", "jacina": "4 mg"},
    {"atk": "C08CA01", "naziv": "Amlodipin 5mg", "oblik": "tableta", "jacina": "5 mg"},
    {"atk": "C09DA01", "naziv": "Losartan 50mg", "oblik": "tableta", "jacina": "50 mg"},
    {"atk": "R03AC02", "naziv": "Salbutamol 100mcg", "oblik": "inhalator", "jacina": "100 mcg/doza"},
]


def mock_drug_search(query: str) -> list[dict]:
    if not query or len(query) < 2:
        return []
    q = query.lower()
    return [d for d in MOCK_LIJEKOVI if q in d["naziv"].lower() or q in d["atk"].lower()]
