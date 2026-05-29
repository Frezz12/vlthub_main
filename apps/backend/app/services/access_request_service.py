from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access_request import ProjectAccessRequest
from app.models.project import Project, ProjectAccess
from app.models.user import User


async def create_request(session: AsyncSession, project_id: str, requester_id: str) -> ProjectAccessRequest:
    existing = await session.execute(
        select(ProjectAccessRequest).where(
            ProjectAccessRequest.project_id == project_id,
            ProjectAccessRequest.requester_id == requester_id,
            ProjectAccessRequest.status == "pending",
        )
    )
    if existing.scalar_one_or_none():
        return None

    req = ProjectAccessRequest(project_id=project_id, requester_id=requester_id)
    session.add(req)
    await session.flush()
    await session.refresh(req)
    return req


async def list_requests(session: AsyncSession, project_id: str) -> list[ProjectAccessRequest]:
    result = await session.execute(
        select(ProjectAccessRequest)
        .where(ProjectAccessRequest.project_id == project_id)
        .order_by(ProjectAccessRequest.created_at.desc())
    )
    return list(result.scalars().all())


async def resolve_request(session: AsyncSession, request_id: str, action: str) -> ProjectAccessRequest | None:
    result = await session.execute(
        select(ProjectAccessRequest).where(ProjectAccessRequest.id == request_id)
    )
    req = result.scalar_one_or_none()
    if not req or req.status != "pending":
        return None

    if action == "approve":
        req.status = "approved"
        access = ProjectAccess(project_id=req.project_id, user_id=req.requester_id, role="viewer")
        session.add(access)
    elif action == "deny":
        req.status = "denied"
    else:
        return None

    await session.flush()
    await session.refresh(req)
    return req


async def resolve_request_by_user(session: AsyncSession, project_id: str, requester_id: str, action: str) -> ProjectAccessRequest | None:
    result = await session.execute(
        select(ProjectAccessRequest).where(
            ProjectAccessRequest.project_id == project_id,
            ProjectAccessRequest.requester_id == requester_id,
            ProjectAccessRequest.status == "pending",
        )
    )
    req = result.scalar_one_or_none()
    if not req:
        return None

    return await resolve_request(session, req.id, action)
