from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AppointmentCreate(BaseModel):
    patient_id: UUID
    doktor_id: UUID
    datum_vrijeme: datetime
    trajanje_minuta: int = 30
    vrsta: str = "pregled"
    napomena: str | None = None


class AppointmentRead(BaseModel):
    id: UUID
    tenant_id: UUID
    patient_id: UUID
    doktor_id: UUID
    datum_vrijeme: datetime
    trajanje_minuta: int
    status: str
    vrsta: str
    napomena: str | None
    patient_ime: str | None = None
    patient_prezime: str | None = None
    doktor_ime: str | None = None
    doktor_prezime: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AppointmentUpdate(BaseModel):
    patient_id: UUID | None = None
    doktor_id: UUID | None = None
    datum_vrijeme: datetime | None = None
    trajanje_minuta: int | None = None
    status: str | None = None
    vrsta: str | None = None
    napomena: str | None = None


class AvailableSlot(BaseModel):
    start: str
    end: str
