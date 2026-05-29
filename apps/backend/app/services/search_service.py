from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


async def search(
    session: AsyncSession,
    q: str,
    type: str = "projects",
    daw: str | None = None,
    role: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Project], int]:
    if type == "projects":
        query = select(Project).where(
            or_(
                Project.title.ilike(f"%{q}%"),
                Project.description.ilike(f"%{q}%"),
            )
        )
        if daw:
            query = query.where(Project.daw_type == daw)
        count_query = select(func.count()).select_from(query.subquery())
        total = await session.scalar(count_query) or 0
        query = query.order_by(Project.updated_at.desc())
        result = await session.execute(query.offset((page - 1) * limit).limit(limit))
        items = list(result.scalars().all())
        return items, total
    return [], 0
