import secrets
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_roles
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import TenantRead, TenantUpdate
from app.services.agent_connection_manager import agent_manager

router = APIRouter(prefix="/settings", tags=["settings"])


class CezihStatusResponse(BaseModel):
    status: str
    sifra_ustanove: str | None
    oid: str | None
    agent_connected: bool
    last_heartbeat: datetime | None


@router.get("/clinic", response_model=TenantRead)
async def get_clinic_settings(
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.get(Tenant, current_user.tenant_id)
    return tenant


@router.patch("/clinic", response_model=TenantRead)
async def update_clinic_settings(
    data: TenantUpdate,
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.get(Tenant, current_user.tenant_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    await db.flush()
    return tenant


@router.get("/cezih-status", response_model=CezihStatusResponse)
async def get_cezih_status(
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.get(Tenant, current_user.tenant_id)
    conn = agent_manager.get(current_user.tenant_id)
    return CezihStatusResponse(
        status=tenant.cezih_status,
        sifra_ustanove=tenant.sifra_ustanove,
        oid=tenant.oid,
        agent_connected=agent_manager.is_connected(current_user.tenant_id),
        last_heartbeat=conn.last_heartbeat if conn else None,
    )


class AgentSecretResponse(BaseModel):
    agent_secret: str


@router.post("/generate-agent-secret", response_model=AgentSecretResponse)
async def generate_agent_secret(
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.get(Tenant, current_user.tenant_id)
    secret = secrets.token_hex(32)
    tenant.agent_secret = secret
    await db.flush()
    return AgentSecretResponse(agent_secret=secret)
