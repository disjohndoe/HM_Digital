import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


async def list_patients(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    search: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Patient], int]:
    base = select(Patient).where(
        Patient.tenant_id == tenant_id,
        Patient.is_active.is_(True),
    )

    if search:
        pattern = f"%{search}%"
        base = base.where(
            or_(
                Patient.ime.ilike(pattern),
                Patient.prezime.ilike(pattern),
                Patient.oib.ilike(pattern),
                Patient.mbo.ilike(pattern),
                Patient.telefon.ilike(pattern),
                Patient.mobitel.ilike(pattern),
            )
        )

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    result = await db.execute(
        base.order_by(Patient.prezime, Patient.ime).offset(skip).limit(limit)
    )
    patients = list(result.scalars().all())

    return patients, total


async def get_patient(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> Patient:
    patient = await db.get(Patient, patient_id)
    if not patient or patient.tenant_id != tenant_id or not patient.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pacijent nije pronadjen")
    return patient


async def create_patient(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: PatientCreate,
) -> Patient:
    if data.oib:
        existing = await db.execute(
            select(Patient).where(
                Patient.oib == data.oib,
                Patient.tenant_id == tenant_id,
                Patient.is_active.is_(True),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Pacijent s tim OIB-om vec postoji",
            )

    if data.mbo:
        existing = await db.execute(
            select(Patient).where(
                Patient.mbo == data.mbo,
                Patient.tenant_id == tenant_id,
                Patient.is_active.is_(True),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Pacijent s tim MBO-om vec postoji",
            )

    patient = Patient(tenant_id=tenant_id, **data.model_dump())
    db.add(patient)
    await db.flush()
    return patient


async def update_patient(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    data: PatientUpdate,
) -> Patient:
    patient = await get_patient(db, tenant_id, patient_id)

    update_data = data.model_dump(exclude_unset=True)

    if "oib" in update_data and update_data["oib"]:
        existing = await db.execute(
            select(Patient).where(
                Patient.oib == update_data["oib"],
                Patient.tenant_id == tenant_id,
                Patient.id != patient_id,
                Patient.is_active.is_(True),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Pacijent s tim OIB-om vec postoji",
            )

    if "mbo" in update_data and update_data["mbo"]:
        existing = await db.execute(
            select(Patient).where(
                Patient.mbo == update_data["mbo"],
                Patient.tenant_id == tenant_id,
                Patient.id != patient_id,
                Patient.is_active.is_(True),
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Pacijent s tim MBO-om vec postoji",
            )

    for field, value in update_data.items():
        setattr(patient, field, value)

    await db.flush()
    return patient


async def delete_patient(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> None:
    patient = await get_patient(db, tenant_id, patient_id)
    patient.is_active = False
