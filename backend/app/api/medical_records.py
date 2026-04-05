import uuid
from datetime import date
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.patient import Patient
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.medical_record import (
    MedicalRecordCreate,
    MedicalRecordRead,
    MedicalRecordUpdate,
)
from app.services import medical_record_service
from app.services.pdf_generator import NalazPDFGenerator
from app.services.pdf_signer import sign_pdf
from app.utils.pagination import PaginatedResponse

router = APIRouter(tags=["medical-records"])


@router.get("/medical-records", response_model=PaginatedResponse[MedicalRecordRead])
async def list_medical_records(
    patient_id: uuid.UUID | None = Query(None),
    tip: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    cezih_sent: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await medical_record_service.list_records(
        db,
        current_user.tenant_id,
        patient_id=patient_id,
        tip=tip,
        date_from=date_from,
        date_to=date_to,
        cezih_sent=cezih_sent,
        skip=skip,
        limit=limit,
        user_role=current_user.role,
    )
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("/medical-records", response_model=MedicalRecordRead, status_code=status.HTTP_201_CREATED)
async def create_medical_record(
    data: MedicalRecordCreate,
    current_user: User = Depends(require_roles("admin", "doctor")),
    db: AsyncSession = Depends(get_db),
):
    return await medical_record_service.create_record(db, current_user.tenant_id, data, current_user.id)


@router.get("/medical-records/{record_id}", response_model=MedicalRecordRead)
async def get_medical_record(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await medical_record_service.get_record(
        db, current_user.tenant_id, record_id, user_role=current_user.role
    )


@router.get("/medical-records/{record_id}/pdf")
async def download_record_pdf(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and download a digitally signed medical finding as a PDF document."""
    record = await medical_record_service.get_record(
        db, current_user.tenant_id, record_id, user_role=current_user.role,
    )

    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ustanova nije pronađena")

    patient = await db.get(Patient, record["patient_id"])
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pacijent nije pronađen")

    doctor = await db.get(User, record["doktor_id"])

    generator = NalazPDFGenerator(
        tenant={
            "naziv": tenant.naziv,
            "vrsta": tenant.vrsta,
            "adresa": tenant.adresa,
            "grad": tenant.grad,
            "postanski_broj": tenant.postanski_broj,
            "oib": tenant.oib,
            "telefon": tenant.telefon,
            "web": tenant.web,
        },
        doctor={
            "ime": doctor.ime if doctor else "",
            "prezime": doctor.prezime if doctor else "",
            "titula": doctor.titula if doctor else "",
        },
        patient={
            "ime": patient.ime,
            "prezime": patient.prezime,
            "datum_rodjenja": patient.datum_rodjenja,
            "spol": patient.spol,
            "oib": patient.oib,
            "mbo": patient.mbo,
            "adresa": patient.adresa,
            "grad": patient.grad,
            "postanski_broj": patient.postanski_broj,
        },
        record=record,
    )

    pdf_bytes = generator.generate()

    titula = doctor.titula if doctor else ""
    ime = doctor.ime if doctor else ""
    prezime_doc = doctor.prezime if doctor else ""
    doctor_name = f"{titula} {ime} {prezime_doc}".strip()
    location = tenant.grad or ""
    try:
        pdf_bytes = await sign_pdf(
            pdf_bytes,
            doctor_name=doctor_name,
            location=location,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Greška pri potpisivanju PDF-a: {e}",
        ) from e

    tip_slug = record.get("tip", "nalaz")
    ime = patient.ime or ""
    prezime = patient.prezime or "pacijent"
    datum = record.get("datum", "")
    short_id = str(record_id)[:4]
    filename = f"{tip_slug}_{ime}_{prezime}_{datum}_{short_id}.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/medical-records/{record_id}", response_model=MedicalRecordRead)
async def update_medical_record(
    record_id: uuid.UUID,
    data: MedicalRecordUpdate,
    current_user: User = Depends(require_roles("admin", "doctor")),
    db: AsyncSession = Depends(get_db),
):
    return await medical_record_service.update_record(db, current_user.tenant_id, record_id, data)
