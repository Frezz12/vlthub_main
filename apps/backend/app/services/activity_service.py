from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.activity import UserActivity
from app.models.user import User


async def log_activity(
    session: AsyncSession,
    user_id: str,
    event_type: str,
    project_id: str | None = None,
    *,
    version_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    activity = UserActivity(
        user_id=user_id,
        event_type=event_type,
        project_id=project_id,
        version_id=version_id,
        details=details,
    )
    session.add(activity)


async def list_project_activities(
    session: AsyncSession,
    project_id: str,
    limit: int = 80,
    offset: int = 0,
) -> list[dict[str, Any]]:
    u = aliased(User)
    result = await session.execute(
        select(UserActivity, u.nickname, u.username, u.avatar_url)
        .join(u, u.id == UserActivity.user_id)
        .where(UserActivity.project_id == project_id)
        .order_by(UserActivity.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    out: list[dict[str, Any]] = []
    for row in result.all():
        act, nickname, username, avatar_url = row
        out.append(
            {
                "id": act.id,
                "event_type": act.event_type,
                "created_at": act.created_at,
                "version_id": act.version_id,
                "details": act.details,
                "user": {
                    "nickname": nickname,
                    "username": username,
                    "avatar_url": avatar_url,
                },
            }
        )
    return out


async def count_project_activities(session: AsyncSession, project_id: str) -> int:
    q = select(func.count()).select_from(UserActivity).where(UserActivity.project_id == project_id)
    n = await session.scalar(q)
    return int(n or 0)


async def get_activity_data(session: AsyncSession, user_id: str, year: int) -> list[dict]:
    start = date(year, 1, 1)
    end = date(year, 12, 31)

    result = await session.execute(
        select(
            func.date(UserActivity.created_at).label("day"),
            func.count(UserActivity.id).label("cnt"),
        )
        .where(
            UserActivity.user_id == user_id,
            func.date(UserActivity.created_at) >= start,
            func.date(UserActivity.created_at) <= end,
        )
        .group_by(func.date(UserActivity.created_at))
        .order_by(func.date(UserActivity.created_at))
    )

    counts_by_day: dict[date, int] = {}
    for row in result:
        counts_by_day[row.day] = row.cnt

    items = []
    current = start
    while current <= end:
        items.append({"date": current.isoformat(), "count": counts_by_day.get(current, 0)})
        current += timedelta(days=1)

    return items
