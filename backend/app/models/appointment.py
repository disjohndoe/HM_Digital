import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseTenantModel


class Appointment(BaseTenantModel):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('zakazan', 'potvrdjen', 'u_tijeku', 'zavrsen', 'otkazan', 'nije_dosao')",
            name="ck_appointment_status",
        ),
        CheckConstraint(
            "vrsta IN ('pregled', 'kontrola', 'lijecenje', 'higijena', 'konzultacija', 'hitno')",
            name="ck_appointment_vrsta",
        ),
        Index("ix_appointments_tenant_date", "tenant_id", "datum_vrijeme"),
        Index("ix_appointments_patient", "tenant_id", "patient_id"),
        Index("ix_appointments_doktor", "tenant_id", "doktor_id", "datum_vrijeme"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    doktor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    datum_vrijeme: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trajanje_minuta: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="zakazan")
    vrsta: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pregled")
    napomena: Mapped[str | None] = mapped_column(Text, nullable=True)
