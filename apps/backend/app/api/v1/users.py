from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.dependencies import get_current_user, get_optional_user
from app.models.badge import Badge, UserBadge
from app.models.project import Project, ProjectCollaborator
from app.models.user import User
from app.models.version import Version
from app.schemas.badge import BadgeOut
from app.schemas.project import ProjectOut
from app.schemas.user import (
    FollowOut,
    SocialLinkOut,
    SocialLinkUpdate,
    UserBadgeBrief,
    UserOut,
    UserProfileOut,
    UserSearchResult,
    UserSettingsUpdate,
    UserUpdate,
)
from app.schemas.activity import ActivityDay, ActivityResponse
from app.services import user_service
from app.services.activity_service import get_activity_data
from app.services.notification_service import create_notification

router = APIRouter(prefix="/users", tags=["users"])


def _get_active_badge(user):
    try:
        ub_list = getattr(user, 'badges', None) or []
    except Exception:
        return None
    active = next((ub for ub in ub_list if ub.is_active), None)
    if active and active.badge:
        return UserBadgeBrief(
            id=active.badge.id,
            name=active.badge.name,
            icon_svg=active.badge.icon_svg,
            description=active.badge.description,
            avatar_ring_gradient=active.badge.avatar_ring_gradient,
            avatar_ring_effect=active.badge.avatar_ring_effect,
            is_active=True,
        )
    return None


def _get_badges(user):
    try:
        ub_list = getattr(user, 'badges', None) or []
    except Exception:
        return []
    return [
        UserBadgeBrief(
            id=ub.badge.id,
            name=ub.badge.name,
            icon_svg=ub.badge.icon_svg,
            description=ub.badge.description,
            avatar_ring_gradient=ub.badge.avatar_ring_gradient,
            avatar_ring_effect=ub.badge.avatar_ring_effect,
            is_active=ub.is_active,
        )
        for ub in ub_list
        if ub.badge
    ]


def _user_to_out(user):
    sl = getattr(user, 'social_links', [])
    return UserOut(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        username=user.username,
        bio=user.bio,
        avatar_url=user.avatar_url,
        cover_url=user.cover_url,
        is_public=user.is_public,
        is_email_confirmed=user.is_email_confirmed,
        created_at=user.created_at,
        social_links=[SocialLinkOut(platform=l.platform, url=l.url) for l in (sl or [])],
        settings=user.settings or {},
        is_admin=user.is_admin,
        storage_limit=user.storage_limit,
        storage_used=user.storage_used,
        badges=_get_badges(user),
        active_badge=_get_active_badge(user),
    )


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return _user_to_out(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    updated = await user_service.update_user(session, user.id, body.model_dump(exclude_unset=True))
    return _user_to_out(updated)


@router.post("/me/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    ext = file.filename.rsplit(".", 1)[-1] if file.filename else "png"
    avatar_rel = f"avatars/{user.id}.{ext}"
    avatar_path = Path(settings.upload_dir).resolve() / avatar_rel
    avatar_path.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    avatar_path.write_bytes(content)
    user.avatar_url = f"/uploads/{avatar_rel}"
    await session.commit()
    return _user_to_out(user)


@router.post("/me/cover", response_model=UserOut)
async def upload_cover(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    ext = file.filename.rsplit(".", 1)[-1] if file.filename else "jpg"
    cover_rel = f"covers/{user.id}.{ext}"
    cover_path = Path(settings.upload_dir).resolve() / cover_rel
    cover_path.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    cover_path.write_bytes(content)
    user.cover_url = f"/uploads/{cover_rel}"
    await session.commit()
    return _user_to_out(user)


@router.patch("/me/social-links", response_model=list[SocialLinkUpdate])
async def update_social_links(
    body: list[SocialLinkUpdate],
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    links = await user_service.update_social_links(session, user.id, [l.model_dump() for l in body])
    return links


@router.get("/me/settings")
async def get_user_settings(user: User = Depends(get_current_user)):
    return user.settings or {}


@router.put("/me/settings")
async def update_user_settings(
    body: UserSettingsUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    user.settings = body.settings
    await session.commit()
    return user.settings


@router.get("/search", response_model=list[UserSearchResult])
async def search_users(
    q: str = Query("", min_length=1),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from sqlalchemy import or_

    result = await session.execute(
        select(User)
        .options(selectinload(User.badges).selectinload(UserBadge.badge))
        .where(
            or_(
                User.username.ilike(f"%{q}%"),
                User.nickname.ilike(f"%{q}%"),
            ),
            or_(
                User.is_public == True,
                User.id == user.id,
            ),
        ).limit(10)
    )
    users = result.scalars().all()
    out = []
    for u in users:
        is_following = await user_service.is_following(session, user.id, u.id)
        out.append(UserSearchResult(
            id=u.id,
            nickname=u.nickname,
            username=u.username,
            avatar_url=u.avatar_url,
            is_following=is_following,
            active_badge=_get_active_badge(u),
        ))
    return out


@router.get("/{username}", response_model=UserProfileOut)
async def get_user_profile(
    username: str,
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_optional_user),
):
    from sqlalchemy import func, select
    from sqlalchemy.orm import selectinload

    result = await session.execute(
        select(User)
        .options(selectinload(User.social_links))
        .options(selectinload(User.badges).selectinload(UserBadge.badge))
        .where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_public and (not current_user or user.id != current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    project_count = await session.scalar(
        select(func.count()).select_from(Project).where(Project.owner_id == user.id)
    ) or 0

    version_count = await session.scalar(
        select(func.count())
        .select_from(Version)
        .join(Project, Version.project_id == Project.id)
        .where(Project.owner_id == user.id)
    ) or 0

    collab_count = await session.scalar(
        select(func.count())
        .select_from(Project)
        .join(Project.collaborators)
        .where(ProjectCollaborator.user_id == user.id)
    ) or 0

    follower_count = await user_service.get_follower_count(session, user.id)
    following_count = await user_service.get_following_count(session, user.id)
    is_following = await user_service.is_following(session, current_user.id, user.id) if current_user else False

    project_filter = [Project.owner_id == user.id]
    if not current_user or user.id != current_user.id:
        project_filter.append(Project.is_public == True)

    projects_result = await session.execute(
        select(Project).where(*project_filter).order_by(Project.updated_at.desc()).limit(6)
    )
    projects = projects_result.scalars().all()

    project_ids = [p.id for p in projects]
    version_counts: dict[str, int] = {}
    total_sizes: dict[str, int] = {}
    if project_ids:
        from sqlalchemy import func
        vc_result = await session.execute(
            select(Version.project_id, func.count(Version.id))
            .where(Version.project_id.in_(project_ids))
            .group_by(Version.project_id)
        )
        for pid, cnt in vc_result:
            version_counts[pid] = cnt
        ts_result = await session.execute(
            select(Version.project_id, func.coalesce(func.sum(Version.file_size), 0))
            .where(Version.project_id.in_(project_ids))
            .group_by(Version.project_id)
        )
        for pid, sz in ts_result:
            total_sizes[pid] = sz

    return UserProfileOut(
        id=user.id,
        nickname=user.nickname,
        username=user.username,
        bio=user.bio,
        avatar_url=user.avatar_url,
        cover_url=user.cover_url,
        is_public=user.is_public,
        created_at=user.created_at,
        social_links=[SocialLinkOut(platform=l.platform, url=l.url) for l in (user.social_links or [])],
        active_badge=_get_active_badge(user),
        project_count=project_count,
        version_count=version_count,
        collaboration_count=collab_count,
        follower_count=follower_count,
        following_count=following_count,
        is_following=is_following,
        projects=[
            ProjectOut(
                id=p.id, owner_id=p.owner_id, title=p.title,
                artists=p.artists, sample_rate=p.sample_rate,
                bpm=p.bpm, key=p.key, beatmaker=p.beatmaker,
                status=p.status, description=p.description,
                cover_url=p.cover_url, daw_type=p.daw_type,
                project_path=p.project_path, is_public=p.is_public,
                is_archived=p.is_archived,
                created_at=p.created_at, updated_at=p.updated_at,
                tags=[], version_count=version_counts.get(p.id, 0),
                total_size=total_sizes.get(p.id, 0),
            )
            for p in projects
        ],
    )


@router.get("/{username}/activity", response_model=ActivityResponse)
async def get_user_activity(
    username: str,
    year: int = Query(2026, ge=2020, le=2030),
    session: AsyncSession = Depends(get_session),
    user: User | None = Depends(get_optional_user),
):
    result = await session.execute(select(User).where(User.username == username))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not target.is_public and (not user or target.id != user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    items = await get_activity_data(session, target.id, year)
    total = sum(item["count"] for item in items)
    return ActivityResponse(
        items=[ActivityDay(date=item["date"], count=item["count"]) for item in items],
        total=total,
    )


@router.post("/{username}/follow")
async def follow_user(
    username: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(User).where(User.username == username))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    follow = await user_service.follow_user(session, current_user.id, target.id)
    if not follow:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already following or cannot follow yourself")
    await create_notification(session, target.id, "new_follower", f"{current_user.nickname} подписался на вас", related_user_id=current_user.id)
    return {"detail": "Followed"}


@router.delete("/{username}/follow")
async def unfollow_user(
    username: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(User).where(User.username == username))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    ok = await user_service.unfollow_user(session, current_user.id, target.id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not following")
    return {"detail": "Unfollowed"}


@router.get("/{username}/followers", response_model=list[FollowOut])
async def get_followers(
    username: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(User).where(User.username == username))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    followers = await user_service.get_followers(session, target.id)

    follower_ids = [f.id for f in followers]
    if follower_ids:
        ub_result = await session.execute(
            select(UserBadge).options(selectinload(UserBadge.badge))
            .where(UserBadge.user_id.in_(follower_ids), UserBadge.is_active == True)
        )
        active_badges_map: dict[str, UserBadgeBrief | None] = {}
        for ub in ub_result.scalars().all():
            if ub.badge:
                active_badges_map[ub.user_id] = UserBadgeBrief(id=ub.badge.id, name=ub.badge.name, icon_svg=ub.badge.icon_svg, description=ub.badge.description, avatar_ring_gradient=ub.badge.avatar_ring_gradient, avatar_ring_effect=ub.badge.avatar_ring_effect, is_active=True)
    else:
        active_badges_map = {}

    return [
        FollowOut(
            id=f.id,
            nickname=f.nickname,
            username=f.username,
            avatar_url=f.avatar_url,
            active_badge=active_badges_map.get(f.id),
            followed_at=datetime.now(),
        )
        for f in followers
    ]


@router.get("/{username}/following", response_model=list[FollowOut])
async def get_following(
    username: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(select(User).where(User.username == username))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    following = await user_service.get_following(session, target.id)

    following_ids = [f.id for f in following]
    if following_ids:
        ub_result = await session.execute(
            select(UserBadge).options(selectinload(UserBadge.badge))
            .where(UserBadge.user_id.in_(following_ids), UserBadge.is_active == True)
        )
        active_badges_map: dict[str, UserBadgeBrief | None] = {}
        for ub in ub_result.scalars().all():
            if ub.badge:
                active_badges_map[ub.user_id] = UserBadgeBrief(id=ub.badge.id, name=ub.badge.name, icon_svg=ub.badge.icon_svg, description=ub.badge.description, avatar_ring_gradient=ub.badge.avatar_ring_gradient, avatar_ring_effect=ub.badge.avatar_ring_effect, is_active=True)
    else:
        active_badges_map = {}

    return [
        FollowOut(
            id=f.id,
            nickname=f.nickname,
            username=f.username,
            avatar_url=f.avatar_url,
            active_badge=active_badges_map.get(f.id),
            followed_at=datetime.now(),
        )
        for f in following
    ]
