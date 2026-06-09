from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.api.deps import get_project_or_404
from app.core.config import settings
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.models.project import Project, ProjectAccess, ProjectCollaborator, ProjectUserPath
from app.models.user import User
from app.schemas.access_request import AccessRequestAction, ProjectAccessRequestOut
from app.services import access_request_service
from app.services.notification_service import create_notification
from app.services.project_service import _user_to_brief
from app.schemas.project import (
    AccessUpdate,
    CollaboratorInvite,
    CollaboratorOut,
    CollaboratorUpdate,
    ProjectCreate,
    ProjectListOut,
    ProjectOut,
    ProjectUpdate,
    ShareLinkCreate,
    ShareLinkOut,
    SharedProjectOut,
    UserBrief,
    UserProjectPathUpdate,
)
from app.schemas.user import UserSearchResult
from app.schemas.project_activity import (
    ProjectActivityListOut,
    ProjectActivityOut,
    ProjectActivityUserBrief,
)
from app.services import project_service
from app.services.activity_service import count_project_activities, list_project_activities, log_activity

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectListOut)
async def list_projects(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    daw: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    archived: bool | None = None,
    favorite: bool | None = None,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    projects, total, access_granted_map = await project_service.list_projects(session, user.id, page, limit, daw, tag, q, archived, favorite)
    owner_ids = list({p.owner_id for p in projects})
    owners = {o.id: o for o in await project_service.resolve_owners(session, owner_ids)}
    items = []
    for p in projects:
        tags = [t.tag for t in p.tags] if p.tags else []
        version_count = await project_service.get_version_count(session, p.id)
        total_size = await project_service.get_total_version_size(session, p.id)
        collabs = await project_service.resolve_collaborators(session, p.collaborators or [])
        items.append(ProjectOut(
            id=p.id, owner_id=p.owner_id, title=p.title, artists=p.artists, sample_rate=p.sample_rate, bpm=p.bpm, key=p.key,
            beatmaker=p.beatmaker, status=p.status,
            description=p.description, lyrics=p.lyrics, cover_url=p.cover_url,
            daw_type=p.daw_type, project_path=p.project_path, is_public=p.is_public, is_archived=p.is_archived,
            created_at=p.created_at, updated_at=p.updated_at,
            tags=tags, version_count=version_count, total_size=total_size, collaborators=[CollaboratorOut(**c) for c in collabs],
            owner=owners.get(p.owner_id),
            access_granted_at=access_granted_map.get(p.id),
            is_favorite=p.is_favorite,
            chat_enabled=p.chat_enabled,
        ))
    return ProjectListOut(items=items, total=total, page=page, limit=limit)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    project = await project_service.create_project(session, user.id, body.model_dump())
    await log_activity(session, user.id, "create_project", project.id)
    tags = [t.tag for t in project.tags]
    return ProjectOut(
        id=project.id, owner_id=project.owner_id, title=project.title, artists=project.artists, sample_rate=project.sample_rate,
        bpm=project.bpm, key=project.key, beatmaker=project.beatmaker,
        status=project.status,
        description=project.description, lyrics=project.lyrics, cover_url=project.cover_url,
        daw_type=project.daw_type, project_path=project.project_path,
        is_public=project.is_public, is_archived=project.is_archived, is_favorite=project.is_favorite,
        chat_enabled=project.chat_enabled,
        created_at=project.created_at, updated_at=project.updated_at,
        tags=tags, version_count=0, total_size=0,
        owner=_user_to_brief(user),
    )


@router.post("/{project_id}/cover", response_model=ProjectOut)
async def upload_project_cover(
    project_id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    project = await project_service.get_project(session, project_id)
    if not project or (project.owner_id != user.id and not any(c.user_id == user.id for c in project.collaborators)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    ext = file.filename.rsplit(".", 1)[-1] if file.filename else "jpg"
    cover_rel = f"project_covers/{project_id}.{ext}"
    cover_path = Path(settings.upload_dir).resolve() / cover_rel
    cover_path.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    cover_path.write_bytes(content)
    project.cover_url = f"/uploads/{cover_rel}"
    await session.commit()
    await session.refresh(project)
    tags = [t.tag for t in project.tags] if project.tags else []
    version_count = await project_service.get_version_count(session, project.id)
    total_size = await project_service.get_total_version_size(session, project.id)
    collabs = await project_service.resolve_collaborators(session, project.collaborators or [])
    owner = await project_service.resolve_owner(session, project.owner_id)
    return ProjectOut(
        id=project.id, owner_id=project.owner_id, title=project.title, artists=project.artists, sample_rate=project.sample_rate,
        bpm=project.bpm, key=project.key, beatmaker=project.beatmaker,
        status=project.status,
        description=project.description, lyrics=project.lyrics, cover_url=project.cover_url,
        daw_type=project.daw_type, project_path=project.project_path,
        is_public=project.is_public, is_archived=project.is_archived, is_favorite=project.is_favorite,
        chat_enabled=project.chat_enabled,
        created_at=project.created_at, updated_at=project.updated_at,
        tags=tags, version_count=version_count, total_size=total_size, collaborators=[CollaboratorOut(**c) for c in collabs],
        owner=owner,
    )


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    project = await project_service.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != user.id and not project.is_public:
        has_access = await session.execute(
            select(ProjectAccess).where(
                ProjectAccess.project_id == project_id, ProjectAccess.user_id == user.id
            )
        )
        if not has_access.scalar_one_or_none():
            is_collab = await session.execute(
                select(ProjectCollaborator).where(
                    ProjectCollaborator.project_id == project_id,
                    ProjectCollaborator.user_id == user.id,
                )
            )
            if not is_collab.scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    tags = [t.tag for t in project.tags] if project.tags else []
    version_count = await project_service.get_version_count(session, project.id)
    total_size = await project_service.get_total_version_size(session, project.id)
    collabs = await project_service.resolve_collaborators(session, project.collaborators or [])
    owner = await project_service.resolve_owner(session, project.owner_id)
    access_granted_at = None
    if project.owner_id != user.id:
        access_result = await session.execute(
            select(ProjectAccess.created_at).where(
                ProjectAccess.project_id == project_id,
                ProjectAccess.user_id == user.id,
            ).order_by(ProjectAccess.created_at.desc()).limit(1)
        )
        access_granted_at = access_result.scalar_one_or_none()

    my_path: str | None = None
    path_row = await session.execute(
        select(ProjectUserPath.project_path).where(
            ProjectUserPath.project_id == project_id,
            ProjectUserPath.user_id == user.id,
        )
    )
    my_path = path_row.scalar_one_or_none()

    return ProjectOut(
        id=project.id, owner_id=project.owner_id, title=project.title, artists=project.artists, sample_rate=project.sample_rate,
        bpm=project.bpm, key=project.key, beatmaker=project.beatmaker,
        status=project.status,
        description=project.description, lyrics=project.lyrics, cover_url=project.cover_url,
        daw_type=project.daw_type, project_path=project.project_path,
        is_public=project.is_public, is_archived=project.is_archived, is_favorite=project.is_favorite,
        chat_enabled=project.chat_enabled,
        created_at=project.created_at, updated_at=project.updated_at,
        tags=tags, version_count=version_count, total_size=total_size, collaborators=[CollaboratorOut(**c) for c in collabs],
        owner=owner, access_granted_at=access_granted_at, my_project_path=my_path,
    )


@router.get("/{project_id}/my-path")
async def get_my_project_path(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    row = await session.execute(
        select(ProjectUserPath.project_path).where(
            ProjectUserPath.project_id == project_id,
            ProjectUserPath.user_id == user.id,
        )
    )
    path = row.scalar_one_or_none()
    return {"project_path": path}


@router.put("/{project_id}/my-path")
async def set_my_project_path(
    project_id: str,
    data: UserProjectPathUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    row = await session.execute(
        select(ProjectUserPath).where(
            ProjectUserPath.project_id == project_id,
            ProjectUserPath.user_id == user.id,
        )
    )
    entry = row.scalar_one_or_none()
    if entry:
        entry.project_path = data.project_path
    else:
        entry = ProjectUserPath(
            project_id=project_id,
            user_id=user.id,
            project_path=data.project_path,
        )
        session.add(entry)
    await session.commit()
    return {"project_path": data.project_path}


@router.get("/{project_id}/activity", response_model=ProjectActivityListOut)
async def list_project_activity(
    project_id: str,
    limit: int = Query(80, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    _project: Project = Depends(get_project_or_404),
):
    rows = await list_project_activities(session, project_id, limit=limit, offset=offset)
    total = await count_project_activities(session, project_id)
    items = [
        ProjectActivityOut(
            id=r["id"],
            event_type=r["event_type"],
            created_at=r["created_at"],
            version_id=r["version_id"],
            details=r["details"],
            user=ProjectActivityUserBrief(**r["user"]),
        )
        for r in rows
    ]
    return ProjectActivityListOut(items=items, total=total)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    payload = body.model_dump(exclude_unset=True)
    project = await project_service.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if "is_archived" in payload and project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can archive the project")
    project = await project_service.update_project(session, project_id, payload)
    if payload:
        await log_activity(
            session,
            user.id,
            "update_project",
            project_id,
            details={"fields": sorted(payload.keys())},
        )
    tags = [t.tag for t in project.tags] if project.tags else []
    version_count = await project_service.get_version_count(session, project.id)
    total_size = await project_service.get_total_version_size(session, project.id)
    collabs = await project_service.resolve_collaborators(session, project.collaborators or [])
    owner = await project_service.resolve_owner(session, project.owner_id)
    return ProjectOut(
        id=project.id, owner_id=project.owner_id, title=project.title, artists=project.artists, sample_rate=project.sample_rate,
        bpm=project.bpm, key=project.key, beatmaker=project.beatmaker,
        status=project.status,
        description=project.description, lyrics=project.lyrics, cover_url=project.cover_url,
        daw_type=project.daw_type, project_path=project.project_path,
        is_public=project.is_public, is_archived=project.is_archived, is_favorite=project.is_favorite,
        chat_enabled=project.chat_enabled,
        created_at=project.created_at, updated_at=project.updated_at,
        tags=tags, version_count=version_count, total_size=total_size, collaborators=[CollaboratorOut(**c) for c in collabs],
        owner=owner,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from app.models.project import Project
    from sqlalchemy import select
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can delete this project")
    deleted = await project_service.delete_project(session, project_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


@router.post("/{project_id}/leave", status_code=status.HTTP_200_OK)
async def leave_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from app.models.project import Project
    from sqlalchemy import select
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner cannot leave the project")
    await project_service.leave_project(session, project_id, user.id)
    return {"detail": "You have left the project"}


@router.post("/{project_id}/collaborators")
async def invite_collaborator(
    project_id: str,
    body: CollaboratorInvite,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from app.models.project import Project
    from sqlalchemy import select as sa_select
    result = await session.execute(sa_select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can manage collaborators")

    result = await session.execute(
        select(User).where(
            (User.username == body.email_or_username) | (User.email == body.email_or_username)
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot invite yourself")
    collab = await project_service.add_collaborator(session, project_id, target.id, body.role, user.id)
    await session.commit()
    return {
        "user_id": target.id,
        "nickname": target.nickname,
        "username": target.username,
        "avatar_url": target.avatar_url,
        "role": collab.role,
        "status": collab.status,
    }


@router.get("/{project_id}/collaborators")
async def list_collaborators(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload
    from app.models.project import Project

    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project_model = result.scalar_one_or_none()
    if not project_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    result = await session.execute(
        select(ProjectCollaborator)
        .options(selectinload(ProjectCollaborator.project))
        .where(ProjectCollaborator.project_id == project_id)
    )
    collabs = result.scalars().all()
    out = []
    for c in collabs:
        u_result = await session.execute(select(User).where(User.id == c.user_id))
        u = u_result.scalar_one_or_none()
        if u:
            out.append({
                "user_id": c.user_id,
                "nickname": u.nickname,
                "username": u.username,
                "avatar_url": u.avatar_url,
                "role": c.role,
                "status": c.status,
            })
    return out


@router.patch("/{project_id}/collaborators/{user_id}")
async def update_collaborator(
    project_id: str,
    user_id: str,
    body: CollaboratorUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from app.models.project import Project
    from sqlalchemy import select as sa_select
    result = await session.execute(sa_select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can manage collaborators")
    success = await project_service.update_collaborator(session, project_id, user_id, body.role)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collaborator not found")
    return {"message": "Collaborator updated"}


@router.delete("/{project_id}/collaborators/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_collaborator(
    project_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from app.models.project import Project
    from sqlalchemy import select as sa_select
    result = await session.execute(sa_select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can manage collaborators")
    await project_service.remove_collaborator(session, project_id, user_id)


@router.post("/{project_id}/cover")
async def upload_project_cover(
    project_id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from app.models.project import Project
    from sqlalchemy import select as sa_select
    result = await session.execute(sa_select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not (project.owner_id == user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can change the cover")

    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "png"
    filename = f"{project_id}.{ext}"
    upload_dir = Path("uploads/covers")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / filename
    content = await file.read()
    file_path.write_bytes(content)

    project.cover_url = f"/uploads/covers/{filename}"
    await session.commit()
    return {"cover_url": project.cover_url}


@router.post("/{project_id}/access")
async def add_access(
    project_id: str,
    body: AccessUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from app.models.project import ProjectAccess
    access = ProjectAccess(project_id=project_id, user_id=user.id, role=body.role)
    session.add(access)
    return access


@router.patch("/{project_id}/access/{user_id}")
async def update_access(
    project_id: str,
    user_id: str,
    body: AccessUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from app.models.project import ProjectAccess
    from sqlalchemy import select
    result = await session.execute(
        select(ProjectAccess).where(ProjectAccess.project_id == project_id, ProjectAccess.user_id == user_id)
    )
    access = result.scalar_one_or_none()
    if not access:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access not found")
    access.role = body.role
    return access


@router.delete("/{project_id}/access/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_access(
    project_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from app.models.project import ProjectAccess
    from sqlalchemy import select
    result = await session.execute(
        select(ProjectAccess).where(ProjectAccess.project_id == project_id, ProjectAccess.user_id == user_id)
    )
    access = result.scalar_one_or_none()
    if access:
        await session.delete(access)


@router.post("/{project_id}/share-links", response_model=ShareLinkOut)
async def create_share_link(
    project_id: str,
    body: ShareLinkCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from app.models.project import Project
    from sqlalchemy import select as sa_select
    result = await session.execute(sa_select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can create share links")
    link = await project_service.create_share_link(session, project_id, body.model_dump(exclude_unset=True))
    return link


@router.delete("/{project_id}/share-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_share_link(
    project_id: str,
    link_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    await project_service.delete_share_link(session, link_id)


@router.post("/{project_id}/request-access")
async def request_project_access(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    project = await project_service.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are the owner")

    req = await access_request_service.create_request(session, project_id, user.id)
    if not req:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request already pending")

    owner_result = await session.execute(select(User).where(User.id == project.owner_id))
    owner = owner_result.scalar_one_or_none()
    if owner:
        await create_notification(
            session, owner.id, "access_request",
            f"{user.nickname} запрашивает доступ к проекту «{project.title}»",
            related_user_id=user.id,
            project_id=project_id,
        )

    return {"detail": "Request sent"}


@router.get("/{project_id}/access-requests", response_model=list[ProjectAccessRequestOut])
async def list_access_requests(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    project = await project_service.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can view requests")

    requests = await access_request_service.list_requests(session, project_id)
    out = []
    for req in requests:
        u_result = await session.execute(select(User).where(User.id == req.requester_id))
        requester = u_result.scalar_one_or_none()
        out.append(ProjectAccessRequestOut(
            id=req.id,
            project_id=req.project_id,
            requester_id=req.requester_id,
            requester_nickname=requester.nickname if requester else "",
            requester_username=requester.username if requester else "",
            requester_avatar=requester.avatar_url if requester else None,
            status=req.status,
            created_at=req.created_at,
        ))
    return out


@router.patch("/{project_id}/access-requests/{request_id}")
async def resolve_access_request(
    project_id: str,
    requester_id: str,
    body: AccessRequestAction,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    project = await project_service.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can resolve requests")

    req = await access_request_service.resolve_request_by_user(session, project_id, requester_id, body.action)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending request found")

    if body.action == "approve":
        await create_notification(
            session, req.requester_id, "access_granted",
            f"Вам предоставлен доступ к проекту «{project.title}»",
            related_user_id=user.id,
            project_id=project_id,
        )
    elif body.action == "deny":
        await create_notification(
            session, req.requester_id, "access_denied",
            f"Запрос на доступ к проекту «{project.title}» отклонён",
            related_user_id=user.id,
            project_id=project_id,
        )

    return {"status": req.status}


@router.get("/shared/{token}", response_model=SharedProjectOut)
async def get_shared_project(
    token: str,
    session: AsyncSession = Depends(get_session),
):
    project = await project_service.get_shared_project_by_token(session, token)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found or expired")

    from sqlalchemy import select as sa_select
    from app.models.project import ShareLink as ShareLinkModel
    result = await session.execute(sa_select(ShareLinkModel).where(ShareLinkModel.token == token))
    link = result.scalar_one_or_none()
    role = link.role if link else "viewer"

    owner = await project_service.resolve_owner(session, project.owner_id)

    return SharedProjectOut(
        id=project.id,
        owner=owner,
        title=project.title,
        artists=project.artists,
        sample_rate=project.sample_rate,
        bpm=project.bpm,
        key=project.key,
        beatmaker=project.beatmaker,
        status=project.status,
        description=project.description,
        lyrics=project.lyrics,
        cover_url=project.cover_url,
        daw_type=project.daw_type,
        created_at=project.created_at,
        updated_at=project.updated_at,
        tags=[t.tag for t in project.tags],
        role=role,
    )


@router.patch("/{project_id}/access-requests/by-user/{requester_id}")
async def resolve_access_request_by_user(
    project_id: str,
    requester_id: str,
    body: AccessRequestAction,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    project = await project_service.get_project(session, project_id)
    if not project or project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can resolve requests")

    req = await access_request_service.resolve_request_by_user(session, project_id, requester_id, body.action)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending request found")

    if body.action == "approve":
        await create_notification(
            session, req.requester_id, "access_granted",
            f"Вам предоставлен доступ к проекту «{project.title}»",
            related_user_id=user.id,
            project_id=project_id,
        )
    elif body.action == "deny":
        await create_notification(
            session, req.requester_id, "access_denied",
            f"Запрос на доступ к проекту «{project.title}» отклонён",
            related_user_id=user.id,
            project_id=project_id,
        )

    return {"status": req.status}



