from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.project import ProjectOut
from app.services.search_service import search

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search_endpoint(
    q: str = Query("", min_length=1),
    type: str = Query("projects", pattern="^(projects)$"),
    daw: str | None = None,
    role: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    items, total = await search(session, q, type, daw, role, page, limit)
    results = []
    for item in items:
        results.append({
            "id": item.id,
            "title": item.title,
            "type": "project",
        })
    return {"items": results, "total": total, "page": page, "limit": limit}
