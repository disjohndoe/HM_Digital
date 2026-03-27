from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class InsuranceCheckRequest(BaseModel):
    mbo: str


class InsuranceCheckResponse(BaseModel):
    mock: bool = True
    mbo: str
    ime: str
    prezime: str
    datum_rodjenja: str
    osiguravatelj: str
    status_osiguranja: str
    broj_osiguranja: str


class ENalazRequest(BaseModel):
    patient_id: UUID
    record_id: UUID
    uputnica_id: str | None = None


class ENalazResponse(BaseModel):
    mock: bool = True
    success: bool
    reference_id: str
    sent_at: datetime


class EUputnicaItem(BaseModel):
    mock: bool = True
    id: str
    datum_izdavanja: str
    izdavatelj: str
    svrha: str
    specijalist: str
    status: str


class EUputniceResponse(BaseModel):
    mock: bool = True
    items: list[EUputnicaItem]


class EReceptLijekEntry(BaseModel):
    atk: str
    naziv: str
    kolicina: int = 1
    doziranje: str = ""
    napomena: str = ""


class EReceptRequest(BaseModel):
    patient_id: UUID
    lijekovi: list[EReceptLijekEntry]


class EReceptResponse(BaseModel):
    mock: bool = True
    success: bool
    recept_id: str


class CezihStatusResponse(BaseModel):
    mock: bool = True
    connected: bool
    mode: str
    agent_connected: bool
    last_heartbeat: datetime | None


# --- Feature 1: Activity Log ---


class CezihActivityItem(BaseModel):
    id: str
    action: str
    resource_id: str | None = None
    details: str | None = None
    created_at: datetime
    user_id: str | None = None


class CezihActivityListResponse(BaseModel):
    items: list[CezihActivityItem]
    total: int


# --- Feature 2: Patient CEZIH Summary ---


class PatientCezihInsurance(BaseModel):
    mbo: str | None = None
    status_osiguranja: str | None = None
    osiguravatelj: str | None = None
    last_checked: datetime | None = None


class PatientCezihENalaz(BaseModel):
    record_id: str
    datum: datetime
    tip: str
    reference_id: str | None = None
    cezih_sent_at: datetime | None = None


class PatientCezihERecept(BaseModel):
    recept_id: str
    datum: datetime
    lijekovi: list[str] = []


class PatientCezihSummary(BaseModel):
    mock: bool = True
    insurance: PatientCezihInsurance
    e_nalaz_history: list[PatientCezihENalaz] = []
    e_recept_history: list[PatientCezihERecept] = []


# --- Feature 3: Dashboard Stats ---


class CezihDashboardStats(BaseModel):
    mock: bool = True
    danas_operacije: int = 0
    otvorene_uputnice: int = 2
    zadnja_operacija: datetime | None = None


# --- Feature 4: Drug Search ---


class LijekItem(BaseModel):
    atk: str
    naziv: str
    oblik: str
    jacina: str
