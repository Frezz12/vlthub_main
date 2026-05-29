from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(session: AsyncSession, user_id: str, type: str, message: str, related_user_id: str | None = None, project_id: str | None = None, version_id: str | None = None) -> Notification:
    notif = Notification(user_id=user_id, type=type, message=message, related_user_id=related_user_id, related_project_id=project_id, related_version_id=version_id)
    session.add(notif)
    await session.flush()
    await session.refresh(notif)
    return notif


async def list_notifications(session: AsyncSession, user_id: str) -> tuple[list[Notification], int, int]:
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )
    items = list(result.scalars().all())
    total = len(items)
    unread = sum(1 for n in items if not n.is_read)
    return items, total, unread


async def mark_read(session: AsyncSession, notification_id: str, user_id: str) -> bool:
    result = await session.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
    )
    notif = result.scalar_one_or_none()
    if not notif:
        return False
    notif.is_read = True
    return True


async def mark_all_read(session: AsyncSession, user_id: str) -> int:
    result = await session.execute(
        select(Notification).where(Notification.user_id == user_id, Notification.is_read == False)
    )
    count = 0
    for notif in result.scalars().all():
        notif.is_read = True
        count += 1
    return count
