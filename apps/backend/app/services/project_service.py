from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import (
    Project,
    ProjectAccess,
    ProjectCollaborator,
    ProjectTag,
    ShareLink,
)
from app.models.version import Version
from app.schemas.project import UserBrief


async def _load_project(session: AsyncSession, project_id: str) -> Project | None:
    result = await session.execute(
        select(Project)
        .options(selectinload(Project.tags), selectinload(Project.collaborators))
        .where(Project.id == project_id)
    )
    return result.scalar_one_or_none()


async def create_project(session: AsyncSession, owner_id: str, data: dict) -> Project:
    tags = data.pop("tags", [])
    project = Project(owner_id=owner_id, **data)
    session.add(project)
    await session.flush()
    for tag_name in tags:
        session.add(ProjectTag(project_id=project.id, tag=tag_name))
    session.add(ProjectAccess(project_id=project.id, user_id=owner_id, role="owner"))
    await session.flush()
    loaded = await _load_project(session, project.id)
    if not loaded:
        raise RuntimeError("Failed to load created project")
    return loaded


async def get_project(session: AsyncSession, project_id: str) -> Project | None:
    return await _load_project(session, project_id)


async def list_projects(
    session: AsyncSession,
    user_id: str,
    page: int = 1,
    limit: int = 20,
    daw: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    archived: bool | None = None,
    favorite: bool | None = None,
) -> tuple[list[Project], int, dict[str, datetime]]:
    from sqlalchemy import or_, text, bindparam
    from datetime import datetime

    base_filter = or_(
        Project.owner_id == user_id,
        Project.is_public == True,
        Project.collaborators.any(ProjectCollaborator.user_id == user_id),
        Project.access.any(ProjectAccess.user_id == user_id),
    )

    extra_filters = []
    if daw:
        extra_filters.append(Project.daw_type == daw)
    if tag:
        extra_filters.append(Project.tags.any(ProjectTag.tag == tag))
    if search:
        extra_filters.append(Project.title.ilike(f"%{search}%"))
    if archived is not None:
        extra_filters.append(Project.is_archived == archived)
    if favorite is not None:
        extra_filters.append(Project.is_favorite == favorite)

    all_filters = [base_filter] + extra_filters

    # Count total
    count_query = select(func.count()).select_from(Project).where(*all_filters)
    total = await session.scalar(count_query) or 0

    # Two-part approach:
    # 1. Get owned projects ordered by created_at DESC
    owned_q = (
        select(Project)
        .options(selectinload(Project.tags), selectinload(Project.collaborators))
        .where(Project.owner_id == user_id, *extra_filters)
        .order_by(Project.created_at.desc())
    )
    owned_result = await session.execute(owned_q)
    owned_projects = list(owned_result.scalars().all())

    # 2. Get accessible (non-owned) projects: via collaborator/access grant or public
    access_subq = (
        select(ProjectAccess.created_at)
        .where(
            ProjectAccess.project_id == Project.id,
            ProjectAccess.user_id == user_id,
        )
        .order_by(ProjectAccess.created_at.desc())
        .limit(1)
        .correlate(Project)
        .scalar_subquery()
    )

    access_q = (
        select(Project, access_subq.label("_access_at"))
        .options(selectinload(Project.tags), selectinload(Project.collaborators))
        .where(
            Project.owner_id != user_id,
            or_(
                Project.is_public == True,
                Project.collaborators.any(ProjectCollaborator.user_id == user_id),
                Project.access.any(ProjectAccess.user_id == user_id),
            ),
            *extra_filters,
        )
        .order_by(Project.created_at.desc())
    )

    access_result = await session.execute(access_q)
    access_rows = access_result.all()

    access_granted_map: dict[str, datetime] = {}
    access_projects: list[Project] = []

    for row in access_rows:
        project = row[0]
        access_at = row[1]
        if project.id not in {p.id for p in access_projects}:
            access_projects.append(project)
            if access_at:
                access_granted_map[project.id] = access_at
    all_projects = owned_projects + access_projects

    # Paginate
    start = (page - 1) * limit
    end = start + limit
    paginated = all_projects[start:end] if start < len(all_projects) else []

    return paginated, total, access_granted_map


async def resolve_owner(session: AsyncSession, owner_id: str) -> UserBrief | None:
    owners = await resolve_owners(session, [owner_id])
    return owners[0] if owners else None


async def resolve_owners(session: AsyncSession, owner_ids: list[str]) -> list[UserBrief]:
    from app.models.user import User
    from app.models.badge import UserBadge
    from sqlalchemy.orm import selectinload

    if not owner_ids:
        return []
    result = await session.execute(
        select(User).where(User.id.in_(owner_ids)).options(selectinload(User.badges).selectinload(UserBadge.badge))
    )
    users = result.scalars().all()
    return [
        _user_to_brief(u)
        for u in users
    ]


def _user_to_brief(user) -> UserBrief:
    active_badge = None
    try:
        ub_list = getattr(user, 'badges', None) or []
    except Exception:
        ub_list = []
    active = next((ub for ub in ub_list if ub.is_active), None)
    if active and active.badge:
        from app.schemas.user import UserBadgeBrief
        active_badge = UserBadgeBrief(
            id=active.badge.id,
            name=active.badge.name,
            icon_svg=active.badge.icon_svg,
            description=active.badge.description,
            avatar_ring_gradient=active.badge.avatar_ring_gradient,
            avatar_ring_effect=active.badge.avatar_ring_effect,
            is_active=True,
        )
    return UserBrief(
        id=user.id,
        nickname=user.nickname,
        username=user.username,
        avatar_url=user.avatar_url,
        active_badge=active_badge,
    )


async def get_version_count(session: AsyncSession, project_id: str) -> int:
    result = await session.execute(
        select(func.count()).where(Version.project_id == project_id)
    )
    return result.scalar() or 0


async def get_total_version_size(session: AsyncSession, project_id: str) -> int:
    result = await session.execute(
        select(func.coalesce(func.sum(Version.file_size), 0)).where(Version.project_id == project_id)
    )
    return result.scalar() or 0


async def resolve_collaborators(session: AsyncSession, collabs: list[ProjectCollaborator]) -> list[dict]:
    from app.models.user import User

    if not collabs:
        return []
    user_ids = [c.user_id for c in collabs]
    result = await session.execute(select(User).where(User.id.in_(user_ids)))
    users = {u.id: u for u in result.scalars().all()}
    return [
        {
            "user_id": c.user_id,
            "nickname": users[c.user_id].nickname if c.user_id in users else "Unknown",
            "username": users[c.user_id].username if c.user_id in users else "unknown",
            "avatar_url": users[c.user_id].avatar_url if c.user_id in users else None,
            "role": c.role,
            "status": c.status,
        }
        for c in collabs
    ]


async def update_project(session: AsyncSession, project_id: str, data: dict) -> Project | None:
    result = await session.execute(
        select(Project)
        .options(selectinload(Project.tags), selectinload(Project.collaborators))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        return None
    tags = data.pop("tags", None)
    for key, value in data.items():
        if value is not None and hasattr(project, key):
            setattr(project, key, value)
    if tags is not None:
        old_tags = await session.execute(select(ProjectTag).where(ProjectTag.project_id == project_id))
        for t in old_tags.scalars().all():
            await session.delete(t)
        for tag_name in tags:
            session.add(ProjectTag(project_id=project_id, tag=tag_name))
    await session.flush()
    return await _load_project(session, project_id)


async def delete_project(session: AsyncSession, project_id: str) -> bool:
    from pathlib import Path
    from app.models.version import VersionFile, VersionAudioPreview, VersionComment
    from app.models.user import User
    from app.core.config import settings

    project = await get_project(session, project_id)
    if not project:
        return False

    owner_id = project.owner_id

    # Delete version files from disk
    result = await session.execute(
        select(Version).where(Version.project_id == project_id)
    )
    versions = result.scalars().all()
    total_freed = 0
    for ver in versions:
        if ver.file_size:
            total_freed += ver.file_size
        files_result = await session.execute(
            select(VersionFile).where(VersionFile.version_id == ver.id)
        )
        for f in files_result.scalars().all():
            if f.file_path:
                p = Path(f.file_path)
                if p.exists():
                    p.unlink()
            await session.delete(f)
        previews_result = await session.execute(
            select(VersionAudioPreview).where(VersionAudioPreview.version_id == ver.id)
        )
        for preview in previews_result.scalars().all():
            if preview.file_path:
                p = Path(preview.file_path)
                if p.exists():
                    p.unlink()
            await session.delete(preview)
        comments_result = await session.execute(
            select(VersionComment).where(VersionComment.version_id == ver.id)
        )
        for comment in comments_result.scalars().all():
            await session.delete(comment)

    # Delete project storage directory
    project_dir = Path(settings.upload_dir) / project_id
    if project_dir.exists():
        import shutil
        shutil.rmtree(project_dir)

    # Adjust owner's storage
    if total_freed > 0:
        owner_result = await session.execute(select(User).where(User.id == owner_id))
        owner = owner_result.scalar_one_or_none()
        if owner:
            owner.storage_used = max(0, owner.storage_used - total_freed)

    await session.delete(project)
    return True


async def add_collaborator(session: AsyncSession, project_id: str, user_id: str, role: str, invited_by: str) -> ProjectCollaborator:
    collab = ProjectCollaborator(project_id=project_id, user_id=user_id, role=role, invited_by=invited_by)
    session.add(collab)
    access = ProjectAccess(project_id=project_id, user_id=user_id, role=role)
    session.add(access)
    await session.flush()
    await session.refresh(collab)
    return collab


async def update_collaborator(session: AsyncSession, project_id: str, user_id: str, role: str) -> bool:
    result = await session.execute(
        select(ProjectCollaborator).where(ProjectCollaborator.project_id == project_id, ProjectCollaborator.user_id == user_id)
    )
    collab = result.scalar_one_or_none()
    if not collab:
        return False
    collab.role = role
    return True


async def remove_collaborator(session: AsyncSession, project_id: str, user_id: str) -> bool:
    result = await session.execute(
        select(ProjectCollaborator).where(ProjectCollaborator.project_id == project_id, ProjectCollaborator.user_id == user_id)
    )
    collab = result.scalar_one_or_none()
    if not collab:
        return False
    await session.delete(collab)
    return True


async def create_share_link(session: AsyncSession, project_id: str, data: dict) -> ShareLink:
    import secrets
    import hashlib

    token = secrets.token_urlsafe(32)
    password_hash = None
    if data.get("password"):
        from app.core.security import hash_password
        password_hash = hash_password(data["password"])
    expires_at = None
    if data.get("expires_in_hours"):
        from datetime import datetime, timedelta, timezone
        expires_at = datetime.now(timezone.utc) + timedelta(hours=data["expires_in_hours"])
    link = ShareLink(
        project_id=project_id,
        token=token,
        password_hash=password_hash,
        expires_at=expires_at,
        role=data.get("role", "viewer"),
    )
    session.add(link)
    await session.flush()
    await session.refresh(link)
    return link


async def delete_share_link(session: AsyncSession, link_id: str) -> bool:
    result = await session.execute(select(ShareLink).where(ShareLink.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        return False
    await session.delete(link)
    return True


async def get_shared_project_by_token(session: AsyncSession, token: str) -> Project | None:
    from datetime import datetime, timezone

    result = await session.execute(
        select(ShareLink)
        .options(selectinload(ShareLink.project).selectinload(Project.tags))
        .where(ShareLink.token == token)
    )
    link = result.scalar_one_or_none()
    if not link:
        return None
    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        return None
    return link.project
