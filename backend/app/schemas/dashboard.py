from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DashboardStats(BaseModel):
    danas_termini: int
    ukupno_pacijenti: int
    ovaj_tjedan_termini: int
    novi_pacijenti_mjesec: int
    cezih_status: str


class TodayAppointment(BaseModel):
    id: UUID
    patient_id: UUID
    datum_vrijeme: datetime
    trajanje_minuta: int
    status: str
    vrsta: str
    patient_ime: str | None
    patient_prezime: str | None
    doktor_ime: str | None
    doktor_prezime: str | None

    model_config = {"from_attributes": True}
