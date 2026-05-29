from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.badge import UserBadge
from app.models.version import VersionAudioPreview, VersionComment, VersionFile, VersionTask

from app.core.config import settings

from app.api.deps import get_project_or_404
from app.core.database import get_session
from app.core.dependencies import get_current_user, get_optional_user
from app.models.project import Project
from app.models.user import User
from app.schemas.version import (
    AudioPreviewCreate,
    AudioPreviewOut,
    CommentCreate,
    CommentOut,
    CompareRequest,
    VersionCreate,
    VersionListOut,
    VersionOut,
    VersionTaskCreate,
    VersionTaskOut,
    VersionTaskUpdate,
    VersionUpdate,
    VersionFileOut,
)
from app.services import version_service
from app.services.activity_service import log_activity
from app.services.notification_service import create_notification

router = APIRouter(tags=["versions"])


@router.post("/projects/{project_id}/versions", response_model=VersionOut, status_code=status.HTTP_201_CREATED)
async def create_version(
    project_id: str,
    body: VersionCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    project: Project = Depends(get_project_or_404),
):
    version = await version_service.create_version(session, project_id, user.id, body.model_dump(exclude_unset=True))
    await log_activity(
        session,
        user.id,
        "create_version",
        project_id,
        version_id=version.id,
        details={"version_number": version.version_number, "title": version.title},
    )
    if project.owner_id != user.id:
        await create_notification(
            session,
            project.owner_id,
            "new_version",
            f"{user.nickname} добавил новую версию в проект «{project.title}»",
            related_user_id=user.id,
            project_id=project_id,
            version_id=version.id,
        )
    return VersionOut(
        id=version.id, project_id=version.project_id, version_number=version.version_number,
        title=version.title, description=version.description, created_by=version.created_by,
        file_size=version.file_size, file_hash=version.file_hash, is_current=version.is_current,
        created_at=version.created_at, updated_at=version.updated_at,
    )


@router.post("/projects/{project_id}/versions/{ver_id}/upload", status_code=status.HTTP_200_OK)
async def upload_version_file(
    project_id: str,
    ver_id: str,
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    version = await version_service.get_version(session, ver_id)
    if not version or version.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    from app.services.storage_service import get_version_storage_path
    import hashlib

    content = await file.read()
    file_size = len(content)

    if user.storage_used + file_size > user.storage_limit:
        await create_notification(
            session,
            user.id,
            "storage_limit",
            f"Лимит хранилища исчерпан. Использовано: {user.storage_used // 1_048_576} MB, лимит: {user.storage_limit // 1_048_576} MB",
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Storage limit exceeded. Used: {user.storage_used}, Limit: {user.storage_limit}, Needed: {file_size}",
        )

    storage_path = get_version_storage_path(project_id, ver_id)
    file_path = storage_path / (file.filename or f"version_{version.version_number}.zip")
    file_path.write_bytes(content)

    file_hash = hashlib.sha256(content).hexdigest()

    rel_path = f"{project_id}/{ver_id}/{file.filename or f'version_{version.version_number}.zip'}"
    version.file_path = rel_path
    version.file_size = file_size
    version.file_hash = file_hash

    vf = await version_service.add_version_file(session, ver_id, file.filename or "unknown", file_size, file_path=rel_path, file_hash=file_hash)

    user.storage_used += file_size

    await log_activity(
        session,
        user.id,
        "upload_version_archive",
        project_id,
        version_id=ver_id,
        details={"file_name": file.filename, "file_size": file_size, "file_id": vf.id},
    )

    return {
        "version_id": ver_id,
        "file_name": file.filename,
        "file_size": file_size,
        "file_hash": file_hash,
        "file_id": vf.id,
    }


@router.put("/projects/{project_id}/versions/{ver_id}/upload/chunk", status_code=status.HTTP_200_OK)
async def upload_version_chunk(
    project_id: str,
    ver_id: str,
    file: UploadFile,
    offset: int = 0,
    total_size: int = 0,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    version = await version_service.get_version(session, ver_id)
    if not version or version.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    from app.services.storage_service import get_version_storage_path
    import hashlib

    storage_path = get_version_storage_path(project_id, ver_id) / "chunks"
    storage_path.mkdir(parents=True, exist_ok=True)
    chunk_path = storage_path / f"chunk_{offset}"

    content = await file.read()
    chunk_path.write_bytes(content)

    chunk_count = len(list(storage_path.glob("chunk_*")))
    bytes_received = sum(f.stat().st_size for f in storage_path.glob("chunk_*") if f.is_file())
    is_complete = bytes_received >= total_size and total_size > 0

    result = {
        "received": bytes_received,
        "total": total_size,
        "chunks": chunk_count,
        "complete": is_complete,
    }

    if is_complete:
        if user.storage_used + total_size > user.storage_limit:
            await create_notification(
                session,
                user.id,
                "storage_limit",
                f"Лимит хранилища исчерпан. Использовано: {user.storage_used // 1_048_576} MB, лимит: {user.storage_limit // 1_048_576} MB",
            )
            import shutil
            shutil.rmtree(storage_path, ignore_errors=True)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Storage limit exceeded. Used: {user.storage_used}, Limit: {user.storage_limit}, Needed: {total_size}",
            )

        final_path = get_version_storage_path(project_id, ver_id) / (file.filename or f"version_{version.version_number}.zip")
        with open(final_path, "wb") as out:
            chunk_files = sorted(storage_path.glob("chunk_*"), key=lambda p: int(p.name.replace("chunk_", "")))
            for cf in chunk_files:
                out.write(cf.read_bytes())
                cf.unlink()
        storage_path.rmdir()

        file_hash = hashlib.sha256(final_path.read_bytes()).hexdigest()
        file_size = final_path.stat().st_size

        rel_path = f"{project_id}/{ver_id}/{file.filename or f'version_{version.version_number}.zip'}"
        version.file_path = rel_path
        version.file_size = file_size
        version.file_hash = file_hash

        vf = await version_service.add_version_file(session, ver_id, file.filename or "unknown", file_size, file_path=rel_path, file_hash=file_hash)
        user.storage_used += file_size
        result["file_hash"] = file_hash
        result["file_size"] = file_size
        result["file_id"] = str(vf.id)

        await log_activity(
            session,
            user.id,
            "upload_version_archive_chunked",
            project_id,
            version_id=ver_id,
            details={"file_name": file.filename, "file_size": file_size, "file_id": str(vf.id)},
        )

    return result


@router.get("/projects/{project_id}/versions", response_model=VersionListOut)
async def list_versions(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
    project: Project = Depends(get_project_or_404),
):
    versions, total = await version_service.list_versions(session, project_id)
    items = [
        VersionOut(
            id=v.id, project_id=v.project_id, version_number=v.version_number,
            title=v.title, description=v.description, created_by=v.created_by,
            file_size=v.file_size, file_hash=v.file_hash, is_current=v.is_current,
            created_at=v.created_at, updated_at=v.updated_at, file_count=0,
        )
        for v in versions
    ]
    return VersionListOut(items=items, total=total)


@router.get("/projects/{project_id}/versions/{ver_id}", response_model=VersionOut)
async def get_version(
    project_id: str,
    ver_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    version = await version_service.get_version(session, ver_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    return VersionOut(
        id=version.id, project_id=version.project_id, version_number=version.version_number,
        title=version.title, description=version.description, created_by=version.created_by,
        file_size=version.file_size, file_hash=version.file_hash, is_current=version.is_current,
        created_at=version.created_at, updated_at=version.updated_at, file_count=0,
        audio_previews=[
            AudioPreviewOut(
                id=p.id, file_path=p.file_path, title=p.title,
                duration=p.duration, file_size=p.file_size, created_at=p.created_at,
            )
            for p in (version.audio_previews or [])
        ],
    )


@router.patch("/projects/{project_id}/versions/{ver_id}", response_model=VersionOut)
async def update_version(
    project_id: str,
    ver_id: str,
    body: VersionUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    payload = body.model_dump(exclude_unset=True)
    version = await version_service.update_version(session, ver_id, payload)
    if not version or version.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    if payload:
        await log_activity(
            session,
            user.id,
            "update_version",
            project_id,
            version_id=ver_id,
            details={"fields": sorted(payload.keys())},
        )
    return VersionOut(
        id=version.id, project_id=version.project_id, version_number=version.version_number,
        title=version.title, description=version.description, created_by=version.created_by,
        file_size=version.file_size, file_hash=version.file_hash, is_current=version.is_current,
        created_at=version.created_at, updated_at=version.updated_at,
    )


@router.delete("/projects/{project_id}/versions/{ver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    project_id: str,
    ver_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from app.models.project import Project
    version = await version_service.get_version(session, ver_id)
    if not version or version.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    await log_activity(
        session,
        user.id,
        "delete_version",
        project_id,
        version_id=ver_id,
        details={"version_number": version.version_number, "title": version.title},
    )

    if version.file_size:
        result = await session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if project:
            owner_result = await session.execute(select(User).where(User.id == project.owner_id))
            owner = owner_result.scalar_one_or_none()
            if owner:
                owner.storage_used = max(0, owner.storage_used - version.file_size)

    deleted = await version_service.delete_version(session, ver_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")


@router.patch("/projects/{project_id}/versions/{ver_id}/current")
async def set_current_version(
    project_id: str,
    ver_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    success = await version_service.set_current_version(session, project_id, ver_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    await log_activity(session, user.id, "set_current_version", project_id, version_id=ver_id, details={})
    return {"message": "Current version updated"}


@router.post("/projects/{project_id}/versions/{ver_id}/download")
async def download_version(
    project_id: str,
    ver_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    version = await version_service.get_version(session, ver_id)
    if not version or version.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    file_name = Path(version.file_path).name if version.file_path else f"version_{version.version_number}.zip"
    await log_activity(
        session,
        user.id,
        "download_version_zip",
        project_id,
        version_id=ver_id,
        details={"file_name": file_name},
    )
    dl = f"/uploads/{version.file_path}" if version.file_path else ""
    return {
        "download_url": dl,
        "expires_in": 3600,
        "file_name": file_name,
    }


@router.get("/projects/{project_id}/versions/{ver_id}/files", response_model=list[VersionFileOut])
async def list_version_files(
    project_id: str,
    ver_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    version = await version_service.get_version(session, ver_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")
    files = await version_service.list_version_files(session, ver_id)
    return [
        VersionFileOut(
            id=f.id, version_id=f.version_id, file_name=f.file_name,
            file_size=f.file_size, file_hash=f.file_hash, created_at=f.created_at,
        )
        for f in files
    ]


@router.get("/projects/{project_id}/versions/{ver_id}/files/{file_id}/download")
async def download_version_file(
    project_id: str,
    ver_id: str,
    file_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from fastapi.responses import FileResponse

    result = await session.execute(select(VersionFile).where(VersionFile.id == file_id))
    vf = result.scalar_one_or_none()
    if not vf or vf.version_id != ver_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    ver = await version_service.get_version(session, ver_id)
    if not ver or ver.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    await log_activity(
        session,
        user.id,
        "download_version_file",
        project_id,
        version_id=ver_id,
        details={"file_name": vf.file_name, "file_id": file_id},
    )

    file_path = vf.file_path
    if not file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")
    full_path = Path(settings.upload_dir) / file_path
    if not full_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")
    return FileResponse(str(full_path), filename=vf.file_name, media_type="application/octet-stream")


@router.post("/projects/{project_id}/versions/compare")
async def compare_versions(
    project_id: str,
    body: CompareRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        result = await version_service.compare_versions(session, body.ver1, body.ver2)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return result


@router.post("/projects/{project_id}/versions/{ver_id}/previews", response_model=AudioPreviewOut)
async def upload_preview(
    project_id: str,
    ver_id: str,
    file: UploadFile,
    body: AudioPreviewCreate = Depends(),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    from app.services.storage_service import get_preview_storage_path
    from app.tasks.audio import get_audio_duration
    storage_path = get_preview_storage_path(project_id, ver_id)
    file_path = storage_path / (file.filename or "preview.mp3")
    content = await file.read()
    file_path.write_bytes(content)
    duration = get_audio_duration(str(file_path))
    title = body.title or (file.filename.rsplit('.', 1)[0] if file.filename else None)
    preview = await version_service.create_audio_preview(
        session, ver_id, str(file_path), title,
        file_size=len(content), duration=duration,
    )
    await log_activity(
        session,
        user.id,
        "upload_preview",
        project_id,
        version_id=ver_id,
        details={"preview_id": preview.id, "title": preview.title},
    )
    return AudioPreviewOut(
        id=preview.id, file_path=preview.file_path, title=preview.title,
        duration=preview.duration, file_size=preview.file_size, created_at=preview.created_at,
    )


@router.delete("/projects/{project_id}/versions/{ver_id}/previews/{preview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preview(
    project_id: str,
    ver_id: str,
    preview_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    result = await session.execute(select(VersionAudioPreview).where(VersionAudioPreview.id == preview_id))
    pr = result.scalar_one_or_none()
    if not pr or pr.version_id != ver_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview not found")
    ver = await version_service.get_version(session, ver_id)
    if not ver or ver.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview not found")
    await log_activity(
        session,
        user.id,
        "delete_preview",
        project_id,
        version_id=ver_id,
        details={"preview_id": preview_id, "title": pr.title},
    )
    await version_service.delete_audio_preview(session, preview_id)


@router.get("/projects/{project_id}/versions/{ver_id}/previews/{preview_id}/stream")
async def stream_preview(
    project_id: str,
    ver_id: str,
    preview_id: str,
    session: AsyncSession = Depends(get_session),
    user: User | None = Depends(get_optional_user),
):
    from pathlib import Path
    from fastapi.responses import FileResponse
    result = await session.execute(select(VersionAudioPreview).where(VersionAudioPreview.id == preview_id))
    preview = result.scalar_one_or_none()
    if not preview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preview not found")
    file_path = preview.file_path
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")
    ext = Path(file_path).suffix.lower()
    mime_map = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".aif": "audio/aiff",
        ".aiff": "audio/aiff",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".wma": "audio/x-ms-wma",
    }
    media_type = mime_map.get(ext, "audio/mpeg")
    return FileResponse(file_path, media_type=media_type)


@router.get("/projects/{project_id}/versions/{ver_id}/comments", response_model=list[CommentOut])
async def list_comments(
    project_id: str,
    ver_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    comments = await version_service.list_comments(session, ver_id)
    user_ids = list({c.user_id for c in comments})
    users = {}
    if user_ids:
        u_result = await session.execute(
            select(User).options(selectinload(User.badges).selectinload(UserBadge.badge)).where(User.id.in_(user_ids))
        )
        users = {u.id: u for u in u_result.scalars().all()}
    out = []
    for c in comments:
        u = users.get(c.user_id)
        active_badge = None
        if u:
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
        out.append(CommentOut(
            id=c.id, user_id=c.user_id,
            nickname=u.nickname if u else "Unknown",
            username=u.username if u else "unknown",
            avatar_url=u.avatar_url if u else None,
            active_badge=active_badge,
            text=c.text, created_at=c.created_at,
        ))
    return out


@router.post("/projects/{project_id}/versions/{ver_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    project_id: str,
    ver_id: str,
    body: CommentCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    comment = await version_service.create_comment(session, ver_id, user.id, body.text)
    snippet = (body.text or "")[:200]
    await log_activity(
        session,
        user.id,
        "create_comment",
        project_id,
        version_id=ver_id,
        details={"comment_id": comment.id, "snippet": snippet},
    )
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
    return CommentOut(
        id=comment.id, user_id=comment.user_id,
        nickname=user.nickname, username=user.username, avatar_url=user.avatar_url,
        active_badge=active_badge,
        text=comment.text, created_at=comment.created_at,
    )


@router.delete("/projects/{project_id}/versions/{ver_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    project_id: str,
    ver_id: str,
    comment_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    result = await session.execute(select(VersionComment).where(VersionComment.id == comment_id))
    c = result.scalar_one_or_none()
    if not c or c.version_id != ver_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    ver = await version_service.get_version(session, ver_id)
    if not ver or ver.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    await log_activity(
        session,
        user.id,
        "delete_comment",
        project_id,
        version_id=ver_id,
        details={"comment_id": comment_id},
    )
    await version_service.delete_comment(session, comment_id)


@router.get("/projects/{project_id}/versions/{ver_id}/tasks", response_model=list[VersionTaskOut])
async def list_tasks(
    project_id: str,
    ver_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    tasks = await version_service.list_tasks(session, ver_id)
    return [
        VersionTaskOut(
            id=t.id, version_id=t.version_id, text=t.text,
            is_done=t.is_done, position=t.position, created_at=t.created_at,
        )
        for t in tasks
    ]


@router.post("/projects/{project_id}/versions/{ver_id}/tasks", response_model=VersionTaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: str,
    ver_id: str,
    body: VersionTaskCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    task = await version_service.create_task(session, ver_id, body.text)
    await log_activity(
        session,
        user.id,
        "create_task",
        project_id,
        version_id=ver_id,
        details={"task_id": task.id, "text": (body.text or "")[:120]},
    )
    return VersionTaskOut(
        id=task.id, version_id=task.version_id, text=task.text,
        is_done=task.is_done, position=task.position, created_at=task.created_at,
    )


@router.patch("/projects/{project_id}/versions/{ver_id}/tasks/{task_id}", response_model=VersionTaskOut)
async def update_task(
    project_id: str,
    ver_id: str,
    task_id: str,
    body: VersionTaskUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    task = await version_service.update_task(session, task_id, body.model_dump(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if body.is_done:
        await log_activity(
            session,
            user.id,
            "complete_task",
            project_id,
            version_id=ver_id,
            details={"task_id": task_id},
        )
    return VersionTaskOut(
        id=task.id, version_id=task.version_id, text=task.text,
        is_done=task.is_done, position=task.position, created_at=task.created_at,
    )


@router.delete("/projects/{project_id}/versions/{ver_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    project_id: str,
    ver_id: str,
    task_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    result = await session.execute(select(VersionTask).where(VersionTask.id == task_id))
    t = result.scalar_one_or_none()
    if not t or t.version_id != ver_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    ver = await version_service.get_version(session, ver_id)
    if not ver or ver.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await log_activity(
        session,
        user.id,
        "delete_task",
        project_id,
        version_id=ver_id,
        details={"task_id": task_id},
    )
    deleted = await version_service.delete_task(session, task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
