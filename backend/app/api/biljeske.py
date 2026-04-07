import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.biljeska import BiljeskaCreate, BiljeskaRead, BiljeskaUpdate
from app.services import audit_service, biljeska_service
from app.utils.pagination import PaginatedResponse

router = APIRouter(tags=["biljeske"])


@router.get("/biljeske", response_model=PaginatedResponse[BiljeskaRead])
async def list_biljeske(
    patient_id: uuid.UUID | None = Query(None),
    kategorija: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await biljeska_service.list_biljeske(
        db,
        current_user.tenant_id,
        patient_id=patient_id,
        kategorija=kategorija,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("/biljeske", response_model=BiljeskaRead, status_code=status.HTTP_201_CREATED)
async def create_biljeska(
    data: BiljeskaCreate,
    current_user: User = Depends(require_roles("admin", "doctor")),
    db: AsyncSession = Depends(get_db),
):
    biljeska = await biljeska_service.create_biljeska(db, current_user.tenant_id, data, current_user.id)
    await audit_service.write_audit(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="biljeska_create",
        resource_type="biljeska",
        resource_id=biljeska["id"],
        details={"patient_id": str(data.patient_id), "kategorija": data.kategorija},
    )
    return biljeska


@router.get("/biljeske/{biljeska_id}", response_model=BiljeskaRead)
async def get_biljeska(
    biljeska_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await biljeska_service.get_biljeska(db, current_user.tenant_id, biljeska_id)


@router.patch("/biljeske/{biljeska_id}", response_model=BiljeskaRead)
async def update_biljeska(
    biljeska_id: uuid.UUID,
    data: BiljeskaUpdate,
    current_user: User = Depends(require_roles("admin", "doctor")),
    db: AsyncSession = Depends(get_db),
):
    updated = await biljeska_service.update_biljeska(db, current_user.tenant_id, biljeska_id, data)
    await audit_service.write_audit(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="biljeska_update",
        resource_type="biljeska",
        resource_id=biljeska_id,
        details={"fields_updated": list(data.model_dump(exclude_unset=True).keys())},
    )
    return updated


@router.delete("/biljeske/{biljeska_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_biljeska(
    biljeska_id: uuid.UUID,
    current_user: User = Depends(require_roles("admin", "doctor")),
    db: AsyncSession = Depends(get_db),
):
    await biljeska_service.delete_biljeska(db, current_user.tenant_id, biljeska_id)
    await audit_service.write_audit(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action="biljeska_delete",
        resource_type="biljeska",
        resource_id=biljeska_id,
        details={},
    )
