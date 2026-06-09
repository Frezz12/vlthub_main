from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.models.project import Project, ProjectAccess, ProjectCollaborator
from app.models.user import User
from sqlalchemy import select


async def get_project_or_404(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Project:
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != user.id:
        has_access = await session.execute(
            select(ProjectAccess).where(
                ProjectAccess.project_id == project_id, ProjectAccess.user_id == user.id
            )
        )
        if not has_access.scalar_one_or_none():
            is_collaborator = await session.execute(
                select(ProjectCollaborator).where(
                    ProjectCollaborator.project_id == project_id,
                    ProjectCollaborator.user_id == user.id,
                )
            )
            if not is_collaborator.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return project


async def require_chat_enabled(
    project: Project = Depends(get_project_or_404),
) -> None:
    if not project.chat_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chat is not enabled for this project")
