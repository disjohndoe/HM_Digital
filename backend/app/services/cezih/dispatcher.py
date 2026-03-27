from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services import cezih_mock_service
from app.services.cezih import service as real_service
from app.services.cezih.exceptions import CezihError, CezihSigningError

logger = logging.getLogger(__name__)


def _is_mock() -> bool:
    return settings.CEZIH_MODE == "mock"


async def _write_audit(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    action: str,
    resource_id: UUID | None = None,
    details: dict | None = None,
) -> None:
    from app.models.audit_log import AuditLog

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


# --- Dispatch functions ---
# http_client is always passed but only used in real mode.


async def insurance_check(
    mbo: str,
    *,
    db: AsyncSession | None = None,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
    http_client=None,
) -> dict:
    if _is_mock():
        return await cezih_mock_service.mock_insurance_check(mbo, db=db, user_id=user_id, tenant_id=tenant_id)

    try:
        result = await real_service.check_insurance(http_client, mbo)
    except CezihError as e:
        logger.error("CEZIH insurance check failed: %s", e.message)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message) from e

    result["mock"] = False

    if db and user_id and tenant_id:
        await _write_audit(
            db, tenant_id, user_id,
            action="insurance_check",
            details={"mbo": mbo, "result": result.get("status_osiguranja"), "mode": "real"},
        )

    return result


async def send_enalaz(
    db: AsyncSession,
    tenant_id: UUID,
    patient_id: UUID,
    record_id: UUID,
    *,
    user_id: UUID | None = None,
    uputnica_id: str | None = None,
    http_client=None,
) -> dict:
    if _is_mock():
        return await cezih_mock_service.mock_send_enalaz(
            db, tenant_id, patient_id, record_id,
            user_id=user_id, uputnica_id=uputnica_id,
        )

    from app.models.patient import Patient

    record = await _get_medical_record(db, tenant_id, patient_id, record_id)
    patient = await db.get(Patient, patient_id)
    if not patient or patient.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pacijent nije pronađen")

    patient_data = {
        "mbo": patient.mbo or "",
        "ime": patient.ime,
        "prezime": patient.prezime,
    }
    record_data = {
        "tip": record.tip if record else "nalaz",
        "tip_display": record.tip if record else "Nalaz",
    }

    try:
        result = await real_service.send_enalaz(http_client, patient_data, record_data, uputnica_id)
    except CezihError as e:
        logger.error("CEZIH e-Nalaz send failed: %s", e.message)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message) from e

    ref = result["reference_id"]
    now = datetime.now(UTC)

    if record:
        record.cezih_sent = True
        record.cezih_sent_at = now
        record.cezih_reference_id = ref
        await db.flush()

    if uputnica_id:
        await _close_euputnica(db, tenant_id, uputnica_id)

    details: dict = {
        "patient_id": str(patient_id),
        "record_id": str(record_id),
        "reference_id": ref,
        "mode": "real",
    }
    if uputnica_id:
        details["uputnica_id"] = uputnica_id

    if user_id:
        await _write_audit(db, tenant_id, user_id, action="e_nalaz_send", resource_id=patient_id, details=details)

    result["mock"] = False
    return result


async def retrieve_euputnice(
    *,
    db: AsyncSession | None = None,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
    http_client=None,
) -> dict:
    if _is_mock():
        return await cezih_mock_service.mock_retrieve_euputnice(db=db, user_id=user_id, tenant_id=tenant_id)

    if not db or not tenant_id:
        return {"mock": False, "items": []}

    try:
        items = await real_service.retrieve_euputnice(http_client)
    except CezihError as e:
        logger.error("CEZIH e-Uputnica retrieve failed: %s", e.message)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message) from e

    new_count = 0
    from app.models.cezih_euputnica import CezihEUputnica

    for item in items:
        ext_id = item.get("id", "")
        existing = await db.execute(
            select(CezihEUputnica).where(
                CezihEUputnica.tenant_id == tenant_id,
                CezihEUputnica.external_id == ext_id,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.status = item.get("status", row.status)
        else:
            db.add(CezihEUputnica(
                tenant_id=tenant_id,
                external_id=ext_id,
                datum_izdavanja=item.get("datum_izdavanja", ""),
                izdavatelj=item.get("izdavatelj", ""),
                svrha=item.get("svrha", ""),
                specijalist=item.get("specijalist", ""),
                status=item.get("status", "Otvorena"),
            ))
            new_count += 1

    await db.flush()

    if user_id:
        await _write_audit(
            db, tenant_id, user_id,
            action="e_uputnica_retrieve",
            details={"count": len(items), "new": new_count, "mode": "real"},
        )

    return await get_stored_euputnice(db, tenant_id, mock=False)


async def get_stored_euputnice(
    db: AsyncSession | None,
    tenant_id: UUID | None,
    mock: bool = True,
) -> dict:
    """Read all persisted e-Uputnice for the tenant."""
    if not db or not tenant_id:
        return {"mock": mock, "items": []}

    from app.models.cezih_euputnica import CezihEUputnica

    result = await db.execute(
        select(CezihEUputnica)
        .where(CezihEUputnica.tenant_id == tenant_id)
        .order_by(CezihEUputnica.datum_izdavanja.desc())
    )
    rows = result.scalars().all()

    items = [
        {
            "mock": mock,
            "id": r.external_id,
            "datum_izdavanja": r.datum_izdavanja,
            "izdavatelj": r.izdavatelj,
            "svrha": r.svrha,
            "specijalist": r.specijalist,
            "status": r.status,
        }
        for r in rows
    ]
    return {"mock": mock, "items": items}


async def send_erecept(
    patient_id: UUID,
    lijekovi: list[dict],
    *,
    db: AsyncSession | None = None,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
    http_client=None,
) -> dict:
    if _is_mock():
        return await cezih_mock_service.mock_send_erecept(
            patient_id, lijekovi, db=db, user_id=user_id, tenant_id=tenant_id,
        )

    from app.models.patient import Patient

    patient = await db.get(Patient, patient_id) if db else None
    patient_data = {
        "mbo": patient.mbo or "" if patient else "",
        "ime": patient.ime if patient else "",
        "prezime": patient.prezime if patient else "",
    }

    try:
        result = await real_service.send_erecept(http_client, patient_data, lijekovi)
    except CezihError as e:
        logger.error("CEZIH e-Recept send failed: %s", e.message)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message) from e

    recept_id = result["recept_id"]

    if db and user_id and tenant_id:
        await _write_audit(
            db, tenant_id, user_id,
            action="e_recept_send",
            resource_id=patient_id,
            details={
                "patient_id": str(patient_id),
                "recept_id": recept_id,
                "lijekovi": [item.get("naziv", "") if isinstance(item, dict) else str(item) for item in lijekovi],
                "mode": "real",
            },
        )

    result["mock"] = False
    return result


async def cezih_status(tenant_id=None, *, http_client=None) -> dict:
    if _is_mock():
        mock_result = cezih_mock_service.mock_cezih_status(tenant_id)
        mock_result["mode"] = settings.CEZIH_MODE
        return mock_result

    # Real mode
    connected = False
    if http_client:
        try:
            connected = await real_service.get_status(http_client)
            connected = connected.get("connected", False)
        except CezihError:
            connected = False

    from app.services.agent_connection_manager import agent_manager

    agent_connected = False
    last_heartbeat = None
    if tenant_id:
        agent_connected = agent_manager.is_connected(tenant_id)
        conn = agent_manager.get(tenant_id)
        if conn:
            last_heartbeat = conn.last_heartbeat

    return {
        "mock": False,
        "connected": connected,
        "mode": "real",
        "agent_connected": agent_connected,
        "last_heartbeat": last_heartbeat,
    }


def drug_search(query: str) -> list[dict]:
    """Drug search — always mock (real needs local DB sync of code lists)."""
    return cezih_mock_service.mock_drug_search(query)


# --- Helpers ---


async def _get_medical_record(db: AsyncSession, tenant_id: UUID, patient_id: UUID, record_id: UUID):
    from app.models.medical_record import MedicalRecord

    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.id == record_id,
            MedicalRecord.tenant_id == tenant_id,
            MedicalRecord.patient_id == patient_id,
        )
    )
    return result.scalar_one_or_none()


async def _close_euputnica(db: AsyncSession, tenant_id: UUID, uputnica_id: str) -> None:
    from app.models.cezih_euputnica import CezihEUputnica

    result = await db.execute(
        select(CezihEUputnica).where(
            CezihEUputnica.tenant_id == tenant_id,
            CezihEUputnica.external_id == uputnica_id,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        row.status = "Zatvorena"
        await db.flush()


# --- Signing dispatch ---


async def sign_document(
    document_bytes: bytes | str,
    *,
    document_id: str | None = None,
    http_client=None,
) -> dict:
    if _is_mock():
        return cezih_mock_service.mock_sign_document(document_id=document_id)

    if not http_client:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="HTTP client not available")

    from app.services.cezih_signing import sign_document as real_sign_document

    try:
        result = await real_sign_document(
            http_client, document_bytes, document_id=document_id,
        )
    except CezihSigningError as e:
        logger.error("CEZIH signing failed: %s", e.message)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.message) from e

    result["mock"] = False
    return result


async def signing_health_check(*, http_client=None) -> dict:
    if _is_mock():
        return cezih_mock_service.mock_sign_health_check()

    if not http_client:
        return {"reachable": False, "reason": "HTTP client not available"}

    from app.services.cezih_signing import sign_health_check as real_health_check

    try:
        return await real_health_check(http_client)
    except Exception as e:
        logger.error("CEZIH signing health check failed: %s", e)
        return {"reachable": False, "reason": str(e)}
