from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_enforcement import get_current_usage
from app.database import get_db
from app.dependencies import require_roles
from app.models.tenant import Tenant
from app.models.user import User

router = APIRouter(prefix="/plan", tags=["plan"])

VALID_PLAN_TIERS = ("solo", "poliklinika", "poliklinika_plus")


class PlanTierChange(BaseModel):
    plan_tier: str
    clear_trial: bool = True

    @field_validator("plan_tier")
    @classmethod
    def validate_plan_tier(cls, v: str) -> str:
        if v not in VALID_PLAN_TIERS:
            raise ValueError(f"Neispravan plan. Dozvoljeni: {', '.join(VALID_PLAN_TIERS)}")
        return v


class TrialExtendRequest(BaseModel):
    additional_days: int

    @field_validator("additional_days")
    @classmethod
    def validate_days(cls, v: int) -> int:
        if v < 1 or v > 90:
            raise ValueError("additional_days mora biti između 1 i 90")
        return v


@router.get("/usage")
async def plan_usage(
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    return await get_current_usage(db, current_user.tenant_id)


@router.patch("/tier")
async def change_plan_tier(
    body: PlanTierChange,
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Klinika nije pronađena")

    old_tier = tenant.plan_tier
    tenant.plan_tier = body.plan_tier

    if body.clear_trial or old_tier == "trial":
        tenant.trial_expires_at = None

    await db.flush()
    return {"plan_tier": tenant.plan_tier, "trial_expires_at": tenant.trial_expires_at}


@router.patch("/trial-extend")
async def extend_trial(
    body: TrialExtendRequest,
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Klinika nije pronađena")

    if tenant.plan_tier != "trial":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Samo trial klijenti mogu produžiti trial",
        )

    base = tenant.trial_expires_at or datetime.now(UTC)
    if base < datetime.now(UTC):
        base = datetime.now(UTC)
    tenant.trial_expires_at = base + timedelta(days=body.additional_days)

    await db.flush()
    return {"trial_expires_at": tenant.trial_expires_at.isoformat()}
