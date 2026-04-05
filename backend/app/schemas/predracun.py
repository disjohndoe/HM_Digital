import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class PredracunCreate(BaseModel):
    patient_id: uuid.UUID
    performed_procedure_ids: list[uuid.UUID] = Field(..., min_length=1)
    napomena: str | None = None


class PredracunStavkaRead(BaseModel):
    id: uuid.UUID
    sifra: str
    naziv: str
    datum: date
    cijena_cents: int

    model_config = {"from_attributes": True}


class PredracunRead(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    broj: str
    datum: date
    ukupno_cents: int
    napomena: str | None
    created_at: datetime
    stavke: list[PredracunStavkaRead] = []

    model_config = {"from_attributes": True}
