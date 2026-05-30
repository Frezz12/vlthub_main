from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete as sa_delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.models.user import User, Follow
from app.models.project import Project, ProjectCollaborator, ProjectAccess
from app.models.version import Version, VersionComment, VersionFile, VersionAudioPreview
from app.models.activity import UserActivity
from app.models.notification import Notification, UserNotificationSetting
from app.models.auth import RefreshToken, EmailConfirmation
from app.models.access_request import ProjectAccessRequest
from app.models.badge import Badge, UserBadge
from app.schemas.user import SetStorageLimit, StorageSummaryOut, UserAdminOut
from app.schemas.badge import BadgeCreate, BadgeOut, BadgeUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


@router.get("/users", response_model=list[UserAdminOut])
async def admin_list_users(
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    result = await session.execute(
        select(User).options(selectinload(User.badges).selectinload(UserBadge.badge)).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return [
        _admin_user_to_out(u)
        for u in users
    ]


def _admin_user_to_out(u) -> UserAdminOut:
    active_badge = None
    try:
        ub_list = getattr(u, 'badges', None) or []
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
    return UserAdminOut(
        id=u.id,
        email=u.email,
        nickname=u.nickname,
        username=u.username,
        avatar_url=u.avatar_url,
        is_admin=u.is_admin,
        referral_code=u.referral_code or "",
        referred_by=u.referred_by,
        referrals_count=u.referrals_count or 0,
        storage_limit=u.storage_limit,
        storage_used=u.storage_used,
        created_at=u.created_at,
        active_badge=active_badge,
    )


@router.patch("/users/{user_id}/storage-limit")
async def admin_set_storage_limit(
    user_id: str,
    body: SetStorageLimit,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.storage_limit = body.storage_limit_gb * 1_073_741_824  # GB to bytes
    await session.commit()

    return {
        "user_id": user.id,
        "storage_limit_gb": body.storage_limit_gb,
        "storage_limit_bytes": user.storage_limit,
    }


@router.get("/storage", response_model=StorageSummaryOut)
async def admin_storage_summary(
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    result = await session.execute(
        select(
            func.count(User.id),
            func.coalesce(func.sum(User.storage_used), 0),
            func.coalesce(func.sum(User.storage_limit), 0),
        )
    )
    row = result.one()
    return StorageSummaryOut(
        total_users=row[0],
        total_used=row[1],
        total_limit=row[2],
    )


@router.get("/stats")
async def admin_stats(
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    now = datetime.now(timezone.utc)

    user_count = await session.scalar(select(func.count(User.id)))
    project_count = await session.scalar(select(func.count(Project.id)))
    version_count = await session.scalar(select(func.count(Version.id)))

    storage = await session.execute(
        select(
            func.coalesce(func.sum(User.storage_used), 0),
            func.coalesce(func.sum(User.storage_limit), 0),
        )
    )
    total_used, total_limit = storage.one()

    users_5min = await session.scalar(
        select(func.count(func.distinct(UserActivity.user_id)))
        .where(UserActivity.created_at >= now - timedelta(minutes=5))
    )

    users_30min = await session.scalar(
        select(func.count(func.distinct(UserActivity.user_id)))
        .where(UserActivity.created_at >= now - timedelta(minutes=30))
    )

    versions_today = await session.scalar(
        select(func.count(Version.id))
        .where(Version.created_at >= now - timedelta(hours=24))
    )

    projects_today = await session.scalar(
        select(func.count(Project.id))
        .where(Project.created_at >= now - timedelta(hours=24))
    )

    hour_col = func.date_trunc(text("'hour'"), UserActivity.created_at).label('hour')
    activity_rows = await session.execute(
        select(hour_col, func.count(UserActivity.id))
        .where(UserActivity.created_at >= now - timedelta(hours=24))
        .group_by(text('hour'))
        .order_by(text('hour'))
    )
    activity_chart = [
        {"date": row[0].strftime('%Y-%m-%d %H:00'), "count": row[1]}
        for row in activity_rows.all()
    ]

    return {
        "total_users": user_count or 0,
        "total_projects": project_count or 0,
        "total_versions": version_count or 0,
        "total_storage_used": total_used or 0,
        "total_storage_limit": total_limit or 0,
        "users_online_5min": users_5min or 0,
        "users_online_30min": users_30min or 0,
        "versions_today": versions_today or 0,
        "projects_today": projects_today or 0,
        "activity_chart": activity_chart,
    }


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")

    await session.execute(sa_delete(VersionComment).where(VersionComment.user_id == user_id))
    await session.execute(sa_delete(UserActivity).where(UserActivity.user_id == user_id))
    await session.execute(sa_delete(Notification).where(Notification.user_id == user_id))
    await session.execute(sa_delete(UserNotificationSetting).where(UserNotificationSetting.user_id == user_id))
    await session.execute(sa_delete(RefreshToken).where(RefreshToken.user_id == user_id))
    await session.execute(sa_delete(EmailConfirmation).where(EmailConfirmation.user_id == user_id))
    await session.execute(sa_delete(ProjectAccessRequest).where(ProjectAccessRequest.requester_id == user_id))
    await session.execute(sa_delete(Follow).where(Follow.follower_id == user_id))
    await session.execute(sa_delete(Follow).where(Follow.following_id == user_id))
    await session.execute(sa_delete(ProjectCollaborator).where(ProjectCollaborator.user_id == user_id))
    await session.execute(sa_delete(UserBadge).where(UserBadge.user_id == user_id))
    await session.execute(sa_delete(ProjectAccess).where(ProjectAccess.user_id == user_id))

    projects = await session.execute(
        select(Project).where(Project.owner_id == user_id)
    )
    for project in projects.scalars().all():
        await session.execute(sa_delete(Version).where(Version.project_id == project.id))
        await session.delete(project)

        project_dir = Path(settings.upload_dir).resolve() / project.id
        if project_dir.exists():
            shutil.rmtree(project_dir)

    avatar_path = Path(settings.upload_dir).resolve() / "avatars"
    for f in avatar_path.glob(f"{user_id}.*"):
        f.unlink()

    await session.delete(user)
    await session.commit()

    return {"ok": True}


@router.get("/users/{user_id}", response_model=UserAdminOut)
async def admin_get_user(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    result = await session.execute(
        select(User).options(selectinload(User.badges).selectinload(UserBadge.badge)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _admin_user_to_out(user)


# ───────────────────────── Badge Management ─────────────────────────


@router.get("/badges", response_model=list[BadgeOut])
async def admin_list_badges(
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    result = await session.execute(select(Badge).order_by(Badge.name))
    return result.scalars().all()


@router.post("/badges", response_model=BadgeOut, status_code=status.HTTP_201_CREATED)
async def admin_create_badge(
    body: BadgeCreate,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    badge = Badge(
        name=body.name,
        icon_svg=body.icon_svg,
        description=body.description,
        avatar_ring_gradient=body.avatar_ring_gradient,
        avatar_ring_effect=body.avatar_ring_effect,
    )
    session.add(badge)
    await session.commit()
    await session.refresh(badge)
    return badge


@router.delete("/badges/{badge_id}")
async def admin_delete_badge(
    badge_id: str,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    result = await session.execute(select(Badge).where(Badge.id == badge_id))
    badge = result.scalar_one_or_none()
    if not badge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Badge not found")
    await session.execute(sa_delete(UserBadge).where(UserBadge.badge_id == badge_id))
    await session.delete(badge)
    await session.commit()
    return {"ok": True}


@router.put("/badges/{badge_id}", response_model=BadgeOut)
async def admin_update_badge(
    badge_id: str,
    body: BadgeUpdate,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    result = await session.execute(select(Badge).where(Badge.id == badge_id))
    badge = result.scalar_one_or_none()
    if not badge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Badge not found")

    if body.name is not None:
        badge.name = body.name
    if body.icon_svg is not None:
        badge.icon_svg = body.icon_svg
    badge.description = body.description
    badge.avatar_ring_gradient = body.avatar_ring_gradient
    badge.avatar_ring_effect = body.avatar_ring_effect

    await session.commit()
    await session.refresh(badge)
    return badge


@router.get("/users/{user_id}/badges")
async def admin_get_user_badges(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    result = await session.execute(
        select(UserBadge)
        .options(selectinload(UserBadge.badge))
        .where(UserBadge.user_id == user_id)
    )
    return [
        {"badge": ub.badge, "is_active": ub.is_active}
        for ub in result.scalars().all()
    ]


@router.post("/users/{user_id}/badges/{badge_id}")
async def admin_assign_badge(
    user_id: str,
    badge_id: str,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    user_result = await session.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    badge_result = await session.execute(select(Badge).where(Badge.id == badge_id))
    if not badge_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Badge not found")

    existing = await session.execute(
        select(UserBadge).where(UserBadge.user_id == user_id, UserBadge.badge_id == badge_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Badge already assigned")

    user_badge = UserBadge(user_id=user_id, badge_id=badge_id)
    session.add(user_badge)
    await session.commit()
    return {"ok": True}


@router.delete("/users/{user_id}/badges/{badge_id}")
async def admin_remove_badge(
    user_id: str,
    badge_id: str,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    result = await session.execute(
        select(UserBadge).where(UserBadge.user_id == user_id, UserBadge.badge_id == badge_id)
    )
    user_badge = result.scalar_one_or_none()
    if not user_badge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not have this badge")
    await session.delete(user_badge)
    await session.commit()
    return {"ok": True}
