from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationListOut, NotificationOut
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListOut)
async def list_notifications(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    items, total, unread = await notification_service.list_notifications(session, user.id)
    return NotificationListOut(
        items=[NotificationOut.model_validate(n) for n in items],
        total=total,
        unread_count=unread,
    )


@router.patch("/{id}/read")
async def mark_read(
    id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    success = await notification_service.mark_read(session, id, user.id)
    return {"success": success}


@router.patch("/read-all")
async def mark_all_read(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    count = await notification_service.mark_all_read(session, user.id)
    return {"marked_read": count}
