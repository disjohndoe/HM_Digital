from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class MedicalRecordCreate(BaseModel):
    patient_id: UUID
    appointment_id: UUID | None = None
    datum: date
    tip: str
    dijagnoza_mkb: str | None = None
    dijagnoza_tekst: str | None = None
    sadrzaj: str

    @field_validator("sadrzaj")
    @classmethod
    def validate_sadrzaj(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("Sadržaj mora imati najmanje 10 znakova")
        return v


class MedicalRecordRead(BaseModel):
    id: UUID
    patient_id: UUID
    doktor_id: UUID
    appointment_id: UUID | None
    datum: date
    tip: str
    dijagnoza_mkb: str | None
    dijagnoza_tekst: str | None
    sadrzaj: str
    cezih_sent: bool
    cezih_sent_at: datetime | None
    cezih_reference_id: str | None
    doktor_ime: str | None = None
    doktor_prezime: str | None = None
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MedicalRecordUpdate(BaseModel):
    appointment_id: UUID | None = None
    datum: date | None = None
    tip: str | None = None
    dijagnoza_mkb: str | None = None
    dijagnoza_tekst: str | None = None
    sadrzaj: str | None = None

    @field_validator("sadrzaj")
    @classmethod
    def validate_sadrzaj(cls, v: str | None) -> str | None:
        if v is not None and len(v.strip()) < 10:
            raise ValueError("Sadržaj mora imati najmanje 10 znakova")
        return v
