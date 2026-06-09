from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.models.version import Version, VersionAudioPreview, VersionComment, VersionFile, VersionTask


async def create_version(session: AsyncSession, project_id: str, created_by: str, data: dict) -> Version:
    max_ver = await session.scalar(
        select(func.coalesce(func.max(Version.version_number), 0)).where(Version.project_id == project_id)
    )
    version = Version(
        project_id=project_id,
        version_number=(max_ver or 0) + 1,
        created_by=created_by,
        **data,
    )
    session.add(version)

    prev_current = await session.execute(
        select(Version).where(Version.project_id == project_id, Version.is_current == True)
    )
    for v in prev_current.scalars().all():
        v.is_current = False
    version.is_current = True
    await session.flush()
    await session.refresh(version)
    return version


async def get_version(session: AsyncSession, version_id: str) -> Version | None:
    result = await session.execute(
        select(Version)
        .options(selectinload(Version.audio_previews))
        .where(Version.id == version_id)
    )
    return result.scalar_one_or_none()


async def list_versions(session: AsyncSession, project_id: str) -> tuple[list[Version], int]:
    result = await session.execute(
        select(Version)
        .where(Version.project_id == project_id)
        .order_by(Version.version_number.desc())
    )
    versions = list(result.scalars().all())
    return versions, len(versions)


async def update_version(session: AsyncSession, version_id: str, data: dict) -> Version | None:
    version = await get_version(session, version_id)
    if not version:
        return None
    for key, value in data.items():
        if value is not None and hasattr(version, key):
            setattr(version, key, value)
    return version


async def delete_version(session: AsyncSession, version_id: str) -> bool:
    from pathlib import Path
    version = await get_version(session, version_id)
    if not version:
        return False

    was_current = version.is_current
    project_id = version.project_id
    version_number = version.version_number

    # Delete version files from disk
    files = await list_version_files(session, version_id)
    for f in files:
        if f.file_path:
            p = Path(f.file_path)
            if p.exists():
                p.unlink()
        await session.delete(f)

    # Delete audio previews
    from app.models.version import VersionAudioPreview
    result = await session.execute(
        select(VersionAudioPreview).where(VersionAudioPreview.version_id == version_id)
    )
    for preview in result.scalars().all():
        if preview.file_path:
            p = Path(preview.file_path)
            if p.exists():
                p.unlink()
        await session.delete(preview)

    # Delete comments
    from app.models.version import VersionComment
    result = await session.execute(
        select(VersionComment).where(VersionComment.version_id == version_id)
    )
    for comment in result.scalars().all():
        await session.delete(comment)

    await session.delete(version)

    # If the deleted version was current, make the previous version current
    if was_current:
        # Clear is_current from any remaining versions first
        remaining_current = await session.execute(
            select(Version).where(Version.project_id == project_id, Version.is_current == True)
        )
        for v in remaining_current.scalars().all():
            v.is_current = False
        prev_result = await session.execute(
            select(Version)
            .where(Version.project_id == project_id, Version.version_number < version_number)
            .order_by(Version.version_number.desc())
            .limit(1)
        )
        prev_version = prev_result.scalar_one_or_none()
        if prev_version:
            prev_version.is_current = True

    return True


async def set_current_version(session: AsyncSession, project_id: str, version_id: str) -> bool:
    await session.execute(
        select(Version).where(Version.project_id == project_id, Version.is_current == True)
    )
    prev_current = await session.execute(
        select(Version).where(Version.project_id == project_id, Version.is_current == True)
    )
    for v in prev_current.scalars().all():
        v.is_current = False
    version = await get_version(session, version_id)
    if not version:
        return False
    version.is_current = True
    return True


async def create_comment(session: AsyncSession, version_id: str, user_id: str, text: str) -> VersionComment:
    comment = VersionComment(version_id=version_id, user_id=user_id, text=text)
    session.add(comment)
    await session.flush()
    await session.refresh(comment)
    return comment


async def list_comments(session: AsyncSession, version_id: str) -> list[VersionComment]:
    result = await session.execute(
        select(VersionComment).where(VersionComment.version_id == version_id).order_by(VersionComment.created_at.asc())
    )
    return list(result.scalars().all())


async def delete_comment(session: AsyncSession, comment_id: str) -> bool:
    result = await session.execute(select(VersionComment).where(VersionComment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        return False
    await session.delete(comment)
    return True


async def create_audio_preview(session: AsyncSession, version_id: str, file_path: str, title: str | None = None, file_size: int | None = None, duration: float | None = None) -> VersionAudioPreview:
    preview = VersionAudioPreview(version_id=version_id, file_path=file_path, title=title, file_size=file_size, duration=duration)
    session.add(preview)
    await session.flush()
    await session.refresh(preview)
    return preview


async def delete_audio_preview(session: AsyncSession, preview_id: str) -> bool:
    from pathlib import Path
    result = await session.execute(select(VersionAudioPreview).where(VersionAudioPreview.id == preview_id))
    preview = result.scalar_one_or_none()
    if not preview:
        return False
    if preview.file_path:
        p = Path(preview.file_path)
        if p.exists():
            p.unlink()
    await session.delete(preview)
    return True


async def add_version_file(session: AsyncSession, version_id: str, file_name: str, file_size: int, file_path: str | None = None, file_hash: str | None = None) -> VersionFile:
    vf = VersionFile(version_id=version_id, file_name=file_name, file_size=file_size, file_path=file_path, file_hash=file_hash)
    session.add(vf)
    await session.flush()
    await session.refresh(vf)
    return vf


async def list_version_files(session: AsyncSession, version_id: str) -> list[VersionFile]:
    result = await session.execute(select(VersionFile).where(VersionFile.version_id == version_id))
    return list(result.scalars().all())


async def compare_versions(session: AsyncSession, ver1_id: str, ver2_id: str) -> dict:
    v1 = await get_version(session, ver1_id)
    v2 = await get_version(session, ver2_id)
    if not v1 or not v2:
        raise ValueError("Version not found")
    return {
        "version_1": {"id": v1.id, "version_number": v1.version_number, "title": v1.title, "file_size": v1.file_size, "file_hash": v1.file_hash, "created_at": v1.created_at},
        "version_2": {"id": v2.id, "version_number": v2.version_number, "title": v2.title, "file_size": v2.file_size, "file_hash": v2.file_hash, "created_at": v2.created_at},
        "size_diff": (v2.file_size or 0) - (v1.file_size or 0),
        "hash_match": v1.file_hash == v2.file_hash,
    }


async def create_task(session: AsyncSession, version_id: str, text: str) -> VersionTask:
    max_pos = await session.scalar(
        select(func.coalesce(func.max(VersionTask.position), -1)).where(VersionTask.version_id == version_id)
    )
    task = VersionTask(version_id=version_id, text=text, position=(max_pos or -1) + 1)
    session.add(task)
    await session.flush()
    await session.refresh(task)
    return task


async def list_tasks(session: AsyncSession, version_id: str) -> list[VersionTask]:
    result = await session.execute(
        select(VersionTask)
        .where(VersionTask.version_id == version_id)
        .order_by(VersionTask.position.asc())
    )
    return list(result.scalars().all())


async def update_task(session: AsyncSession, task_id: str, data: dict) -> VersionTask | None:
    result = await session.execute(select(VersionTask).where(VersionTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return None
    for key, value in data.items():
        if value is not None and hasattr(task, key):
            setattr(task, key, value)
    return task


async def delete_task(session: AsyncSession, task_id: str) -> bool:
    result = await session.execute(select(VersionTask).where(VersionTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        return False
    await session.delete(task)
    return True
