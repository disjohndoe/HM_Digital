from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

ALLOWED_KATEGORIJE = {"opca", "anamneza", "dijagnoza", "terapija", "napredak", "ostalo"}


class BiljeskaCreate(BaseModel):
    patient_id: UUID
    datum: date
    naslov: str
    sadrzaj: str
    kategorija: str = "opca"

    @field_validator("naslov")
    @classmethod
    def validate_naslov(cls, v: str) -> str:
        if len(v.strip()) < 1:
            raise ValueError("Naslov je obavezan")
        return v

    @field_validator("sadrzaj")
    @classmethod
    def validate_sadrzaj(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("Sadržaj mora imati najmanje 3 znaka")
        return v

    @field_validator("kategorija")
    @classmethod
    def validate_kategorija(cls, v: str) -> str:
        if v not in ALLOWED_KATEGORIJE:
            raise ValueError(f"Kategorija mora biti jedna od: {', '.join(sorted(ALLOWED_KATEGORIJE))}")
        return v


class BiljeskaRead(BaseModel):
    id: UUID
    patient_id: UUID
    doktor_id: UUID
    datum: date
    naslov: str
    sadrzaj: str
    kategorija: str
    is_pinned: bool
    doktor_ime: str | None = None
    doktor_prezime: str | None = None
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BiljeskaUpdate(BaseModel):
    datum: date | None = None
    naslov: str | None = None
    sadrzaj: str | None = None
    kategorija: str | None = None
    is_pinned: bool | None = None

    @field_validator("naslov")
    @classmethod
    def validate_naslov(cls, v: str | None) -> str | None:
        if v is not None and len(v.strip()) < 1:
            raise ValueError("Naslov je obavezan")
        return v

    @field_validator("sadrzaj")
    @classmethod
    def validate_sadrzaj(cls, v: str | None) -> str | None:
        if v is not None and len(v.strip()) < 3:
            raise ValueError("Sadržaj mora imati najmanje 3 znaka")
        return v

    @field_validator("kategorija")
    @classmethod
    def validate_kategorija(cls, v: str | None) -> str | None:
        if v is not None and v not in ALLOWED_KATEGORIJE:
            raise ValueError(f"Kategorija mora biti jedna od: {', '.join(sorted(ALLOWED_KATEGORIJE))}")
        return v
