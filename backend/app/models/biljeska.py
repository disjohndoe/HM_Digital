import uuid
from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseTenantModel


class Biljeska(BaseTenantModel):
    __tablename__ = "biljeske"
    __table_args__ = (
        Index("ix_biljeske_tenant_patient", "tenant_id", "patient_id", "datum"),
        CheckConstraint(
            "kategorija IN ('opca', 'anamneza', 'dijagnoza', 'terapija', 'napredak', 'ostalo')",
            name="ck_biljeska_kategorija",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    doktor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    datum: Mapped[date] = mapped_column(Date, nullable=False)
    naslov: Mapped[str] = mapped_column(String(200), nullable=False)
    sadrzaj: Mapped[str] = mapped_column(Text, nullable=False)
    kategorija: Mapped[str] = mapped_column(String(30), nullable=False, server_default="opca")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
