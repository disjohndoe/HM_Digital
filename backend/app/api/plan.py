from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_enforcement import get_current_usage
from app.database import get_db
from app.dependencies import require_roles
from app.models.user import User

router = APIRouter(prefix="/plan", tags=["plan"])


@router.get("/usage")
async def plan_usage(
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    return await get_current_usage(db, current_user.tenant_id)
