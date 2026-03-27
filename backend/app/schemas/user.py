from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.tenant import TenantRead


class UserRead(BaseModel):
    id: UUID
    email: str
    ime: str
    prezime: str
    titula: str | None
    telefon: str | None
    role: str
    is_active: bool
    last_login_at: datetime | None
    tenant_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class UserReadWithTenant(UserRead):
    tenant: TenantRead


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    ime: str
    prezime: str
    titula: str | None = None
    telefon: str | None = None
    role: str = "doctor"


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    ime: str | None = None
    prezime: str | None = None
    titula: str | None = None
    telefon: str | None = None
    role: str | None = None
    is_active: bool | None = None
