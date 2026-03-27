import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_enforcement import check_user_limit
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.utils.pagination import PaginatedResponse
from app.utils.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/doctors", response_model=PaginatedResponse[UserRead])
async def list_doctors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List doctors for the current tenant. Available to all authenticated users."""
    base = select(User).where(
        User.tenant_id == current_user.tenant_id,
        User.role == "doctor",
        User.is_active == True,
    )
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    result = await db.execute(base.offset(skip).limit(limit).order_by(User.prezime, User.ime))
    users = result.scalars().all()

    return PaginatedResponse(items=users, total=total, skip=skip, limit=limit)


@router.get("", response_model=PaginatedResponse[UserRead])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: str | None = Query(None),
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    base = select(User).where(User.tenant_id == current_user.tenant_id)
    if role:
        base = base.where(User.role == role)
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    result = await db.execute(base.offset(skip).limit(limit).order_by(User.created_at))
    users = result.scalars().all()

    return PaginatedResponse(items=users, total=total, skip=skip, limit=limit)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    await check_user_limit(db, current_user.tenant_id)

    existing = await db.execute(
        select(User).where(User.email == data.email, User.tenant_id == current_user.tenant_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email vec postoji u ovoj klinici")

    user = User(
        tenant_id=current_user.tenant_id,
        email=data.email,
        hashed_password=hash_password(data.password),
        ime=data.ime,
        prezime=data.prezime,
        titula=data.titula,
        telefon=data.telefon,
        role=data.role,
    )
    db.add(user)
    await db.flush()
    return user


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user or user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Korisnik nije pronadjen")
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user or user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Korisnik nije pronadjen")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user or user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Korisnik nije pronadjen")

    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ne mozete deaktivirati vlastiti racun")

    user.is_active = False
