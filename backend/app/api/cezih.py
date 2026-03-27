import json  # noqa: F401
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_enforcement import check_cezih_access
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.audit_log import AuditLog
from app.models.cezih_euputnica import CezihEUputnica
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.schemas.cezih import (
    CezihActivityItem,
    CezihActivityListResponse,
    CezihDashboardStats,
    CezihStatusResponse,
    EReceptRequest,
    EReceptResponse,
    ENalazRequest,
    ENalazResponse,
    EUputniceResponse,
    InsuranceCheckRequest,
    InsuranceCheckResponse,
    LijekItem,
    PatientCezihENalaz,
    PatientCezihERecept,
    PatientCezihInsurance,
    PatientCezihSummary,
)
from app.services import cezih_mock_service

router = APIRouter(prefix="/cezih", tags=["cezih"])


@router.get("/status", response_model=CezihStatusResponse)
async def get_cezih_status(
    current_user: User = Depends(get_current_user),
):
    return cezih_mock_service.mock_cezih_status(current_user.tenant_id)


@router.post("/provjera-osiguranja", response_model=InsuranceCheckResponse)
async def provjera_osiguranja(
    data: InsuranceCheckRequest,
    current_user: User = Depends(require_roles("admin", "doctor", "nurse")),
    db: AsyncSession = Depends(get_db),
):
    await check_cezih_access(db, current_user.tenant_id)
    return await cezih_mock_service.mock_insurance_check(
        data.mbo, db=db, user_id=current_user.id, tenant_id=current_user.tenant_id
    )


@router.post("/e-nalaz", response_model=ENalazResponse)
async def send_enalaz(
    data: ENalazRequest,
    current_user: User = Depends(require_roles("admin", "doctor")),
    db: AsyncSession = Depends(get_db),
):
    await check_cezih_access(db, current_user.tenant_id)
    return await cezih_mock_service.mock_send_enalaz(
        db, current_user.tenant_id, data.patient_id, data.record_id,
        user_id=current_user.id, uputnica_id=data.uputnica_id,
    )


@router.get("/e-uputnice", response_model=EUputniceResponse)
async def list_euputnice(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all persisted e-Uputnice for the tenant."""
    return await cezih_mock_service.get_stored_euputnice(
        db=db, tenant_id=current_user.tenant_id,
    )


@router.post("/e-uputnica/preuzmi", response_model=EUputniceResponse)
async def retrieve_euputnice(
    current_user: User = Depends(require_roles("admin", "doctor", "nurse")),
    db: AsyncSession = Depends(get_db),
):
    await check_cezih_access(db, current_user.tenant_id)
    return await cezih_mock_service.mock_retrieve_euputnice(
        db=db, user_id=current_user.id, tenant_id=current_user.tenant_id
    )


@router.post("/e-recept", response_model=EReceptResponse)
async def send_erecept(
    data: EReceptRequest,
    current_user: User = Depends(require_roles("admin", "doctor")),
    db: AsyncSession = Depends(get_db),
):
    await check_cezih_access(db, current_user.tenant_id)
    lijekovi_dicts = [l.model_dump() for l in data.lijekovi]
    return await cezih_mock_service.mock_send_erecept(
        data.patient_id, lijekovi_dicts,
        db=db, user_id=current_user.id, tenant_id=current_user.tenant_id,
    )


# --- Feature 1: Activity Log ---


@router.get("/activity", response_model=CezihActivityListResponse)
async def get_cezih_activity(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(AuditLog).where(
        AuditLog.tenant_id == current_user.tenant_id,
        AuditLog.resource_type == "cezih",
    )

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0

    result = await db.execute(
        base.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    )
    rows = result.scalars().all()

    items = [
        CezihActivityItem(
            id=str(r.id),
            action=r.action,
            resource_id=str(r.resource_id) if r.resource_id else None,
            details=r.details,
            created_at=r.created_at,
            user_id=str(r.user_id) if r.user_id else None,
        )
        for r in rows
    ]

    return CezihActivityListResponse(items=items, total=total)


# --- Feature 2: Patient CEZIH Summary ---


@router.get("/patient/{patient_id}/summary", response_model=PatientCezihSummary)
async def get_patient_cezih_summary(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # e-Nalaz history: medical records sent to CEZIH for this patient
    records_result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.tenant_id == current_user.tenant_id,
            MedicalRecord.patient_id == patient_id,
            MedicalRecord.cezih_sent == True,  # noqa: E712
        ).order_by(MedicalRecord.cezih_sent_at.desc())
    )
    records = records_result.scalars().all()

    e_nalaz_history = [
        PatientCezihENalaz(
            record_id=str(r.id),
            datum=r.cezih_sent_at or r.created_at,
            tip=r.tip,
            reference_id=r.cezih_reference_id,
            cezih_sent_at=r.cezih_sent_at,
        )
        for r in records
    ]

    # e-Recept history from audit log
    recept_result = await db.execute(
        select(AuditLog).where(
            AuditLog.tenant_id == current_user.tenant_id,
            AuditLog.resource_type == "cezih",
            AuditLog.action == "e_recept_send",
            AuditLog.resource_id == patient_id,
        ).order_by(AuditLog.created_at.desc())
    )
    recept_logs = recept_result.scalars().all()

    e_recept_history = []
    for log in recept_logs:
        details = json.loads(log.details) if log.details else {}
        e_recept_history.append(
            PatientCezihERecept(
                recept_id=details.get("recept_id", "—"),
                datum=log.created_at,
                lijekovi=details.get("lijekovi", []),
            )
        )

    # Insurance: find the most recent insurance check in audit log
    ins_result = await db.execute(
        select(AuditLog).where(
            AuditLog.tenant_id == current_user.tenant_id,
            AuditLog.resource_type == "cezih",
            AuditLog.action == "insurance_check",
        ).order_by(AuditLog.created_at.desc()).limit(1)
    )
    ins_log = ins_result.scalar_one_or_none()

    insurance = PatientCezihInsurance()
    if ins_log and ins_log.details:
        ins_details = json.loads(ins_log.details)
        insurance = PatientCezihInsurance(
            mbo=ins_details.get("mbo"),
            status_osiguranja=ins_details.get("result"),
            last_checked=ins_log.created_at,
        )

    return PatientCezihSummary(
        insurance=insurance,
        e_nalaz_history=e_nalaz_history,
        e_recept_history=e_recept_history,
    )


# --- Feature 3: Dashboard Stats ---


@router.get("/dashboard-stats", response_model=CezihDashboardStats)
async def get_cezih_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's CEZIH operations count
    count_result = await db.execute(
        select(func.count()).where(
            AuditLog.tenant_id == current_user.tenant_id,
            AuditLog.resource_type == "cezih",
            AuditLog.created_at >= today_start,
        )
    )
    danas = count_result.scalar() or 0

    # Most recent CEZIH operation
    last_result = await db.execute(
        select(AuditLog.created_at).where(
            AuditLog.tenant_id == current_user.tenant_id,
            AuditLog.resource_type == "cezih",
        ).order_by(AuditLog.created_at.desc()).limit(1)
    )
    last_op = last_result.scalar_one_or_none()

    # Open referrals count from persisted data
    open_result = await db.execute(
        select(func.count()).where(
            CezihEUputnica.tenant_id == current_user.tenant_id,
            CezihEUputnica.status == "Otvorena",
        )
    )
    open_count = open_result.scalar() or 0

    return CezihDashboardStats(
        danas_operacije=danas,
        otvorene_uputnice=open_count,
        zadnja_operacija=last_op,
    )


# --- Feature 4: Drug Search ---


@router.get("/lijekovi", response_model=list[LijekItem])
async def search_drugs(
    q: str = Query("", min_length=0),
    current_user: User = Depends(get_current_user),
):
    return cezih_mock_service.mock_drug_search(q)
