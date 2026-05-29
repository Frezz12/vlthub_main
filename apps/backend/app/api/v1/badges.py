from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.models.badge import Badge, UserBadge
from app.models.user import User
from app.schemas.badge import UserBadgeOut

router = APIRouter(prefix="/users/me/badges", tags=["badges"])


@router.get("", response_model=list[UserBadgeOut])
async def get_my_badges(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(UserBadge)
        .options(selectinload(UserBadge.badge))
        .where(UserBadge.user_id == user.id)
    )
    user_badges = result.scalars().all()
    return [
        UserBadgeOut(
            badge=ub.badge,
            is_active=ub.is_active,
        )
        for ub in user_badges
    ]


@router.post("/{badge_id}/activate")
async def activate_badge(
    badge_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(UserBadge)
        .options(selectinload(UserBadge.badge))
        .where(UserBadge.user_id == user.id, UserBadge.badge_id == badge_id)
    )
    user_badge = result.scalar_one_or_none()
    if not user_badge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Badge not assigned to you")

    all_ubs = await session.execute(
        select(UserBadge).where(UserBadge.user_id == user.id)
    )
    for ub in all_ubs.scalars().all():
        ub.is_active = False

    user_badge.is_active = True
    await session.commit()

    return {"ok": True, "badge_id": badge_id}


@router.post("/deactivate")
async def deactivate_badge(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(UserBadge).where(UserBadge.user_id == user.id, UserBadge.is_active == True)
    )
    for ub in result.scalars().all():
        ub.is_active = False
    await session.commit()

    return {"ok": True}
