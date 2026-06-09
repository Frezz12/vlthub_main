import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.chat import ChatMessage, ChatRoom
from app.models.user import User
from app.models.badge import UserBadge
from app.schemas.chat import ChatMessageOut

CHAT_FILE_MAX_SIZE = 100 * 1024 * 1024


async def get_or_create_room(session: AsyncSession, project_id: str) -> ChatRoom:
    result = await session.execute(
        select(ChatRoom).where(ChatRoom.project_id == project_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        room = ChatRoom(project_id=project_id)
        session.add(room)
        await session.commit()
        await session.refresh(room)
    return room


async def _load_message(session: AsyncSession, message_id: str) -> ChatMessage:
    result = await session.execute(
        select(ChatMessage)
        .options(
            selectinload(ChatMessage.user).selectinload(User.badges).selectinload(UserBadge.badge),
            selectinload(ChatMessage.version),
            selectinload(ChatMessage.reply_to).selectinload(ChatMessage.user).selectinload(User.badges).selectinload(UserBadge.badge),
        )
        .where(ChatMessage.id == message_id)
    )
    return result.scalar_one()


async def create_message(
    session: AsyncSession, project_id: str, user_id: str, content: str, reply_to_id: str | None = None
) -> ChatMessage:
    room = await get_or_create_room(session, project_id)
    message = ChatMessage(room_id=room.id, user_id=user_id, content=content, reply_to_id=reply_to_id)
    session.add(message)
    await session.commit()
    return await _load_message(session, message.id)


async def create_file_message(
    session: AsyncSession, project_id: str, user_id: str, content: str, file_name: str, file_data: bytes, reply_to_id: str | None = None
) -> ChatMessage:
    file_size = len(file_data)
    file_ext = file_name.rsplit(".", 1)[-1] if "." in file_name else ""

    message_id = str(uuid.uuid4())
    storage_rel = f"chat/{project_id}/{message_id}/{file_name}"
    storage_path = (Path(settings.upload_dir).resolve() / storage_rel)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_bytes(file_data)

    room = await get_or_create_room(session, project_id)
    message = ChatMessage(
        id=message_id,
        room_id=room.id,
        user_id=user_id,
        content=content,
        file_name=file_name,
        file_path=f"/uploads/{storage_rel}",
        file_size=file_size,
        file_type=file_ext,
        reply_to_id=reply_to_id,
    )
    session.add(message)
    await session.commit()
    return await _load_message(session, message.id)


async def create_version_message(
    session: AsyncSession, project_id: str, user_id: str, content: str, version_id: str, reply_to_id: str | None = None
) -> ChatMessage:
    room = await get_or_create_room(session, project_id)
    message = ChatMessage(
        room_id=room.id,
        user_id=user_id,
        content=content,
        version_id=version_id,
        reply_to_id=reply_to_id,
    )
    session.add(message)
    await session.commit()
    return await _load_message(session, message.id)


async def update_message(
    session: AsyncSession, message_id: str, user_id: str, content: str
) -> ChatMessage:
    result = await session.execute(
        select(ChatMessage).where(ChatMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if message.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit another user's message")
    message.content = content
    message.edited_at = datetime.now(timezone.utc)
    await session.commit()
    return await _load_message(session, message.id)


async def delete_message(
    session: AsyncSession, message_id: str, user_id: str, scope: str = "all"
) -> None:
    result = await session.execute(
        select(ChatMessage).where(ChatMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if scope == "all":
        if message.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete another user's message")
        await session.delete(message)
    else:
        deleted_by = message.deleted_by or []
        if user_id not in deleted_by:
            deleted_by.append(user_id)
        message.deleted_by = deleted_by
    await session.commit()


async def toggle_reaction(
    session: AsyncSession, message_id: str, user_id: str, emoji: str
) -> ChatMessage:
    result = await session.execute(
        select(ChatMessage)
        .options(
            selectinload(ChatMessage.user).selectinload(User.badges).selectinload(UserBadge.badge),
        )
        .where(ChatMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    reactions = dict(message.reactions) if message.reactions else {}
    users = list(reactions.get(emoji, []))
    if user_id in users:
        users.remove(user_id)
        if not users:
            reactions.pop(emoji, None)
        else:
            reactions[emoji] = users
    else:
        users.append(user_id)
        reactions[emoji] = users
    message.reactions = reactions
    await session.commit()
    return message


async def get_messages(
    session: AsyncSession, project_id: str, user_id: str, limit: int = 50, offset: int = 0
) -> tuple[list[ChatMessage], int]:
    room = await get_or_create_room(session, project_id)
    total_result = await session.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.room_id == room.id)
    )
    total = total_result.scalar() or 0
    result = await session.execute(
        select(ChatMessage)
        .options(
            selectinload(ChatMessage.user).selectinload(User.badges).selectinload(UserBadge.badge),
            selectinload(ChatMessage.version),
            selectinload(ChatMessage.reply_to).selectinload(ChatMessage.user).selectinload(User.badges).selectinload(UserBadge.badge),
        )
        .where(ChatMessage.room_id == room.id)
        .order_by(ChatMessage.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))
    # filter out messages deleted by this user
    messages = [m for m in messages if not (m.deleted_by and user_id in m.deleted_by)]
    total = len(messages) + offset
    return messages, total


def _get_active_badge(user):
    if not user or not user.badges:
        return None
    for ub in user.badges:
        if ub.is_active and ub.badge:
            return ub.badge
    return None


def message_to_out(message: ChatMessage) -> ChatMessageOut:
    badge = _get_active_badge(message.user)

    return ChatMessageOut(
        id=message.id,
        room_id=message.room_id,
        user_id=message.user_id,
        user_name=message.user.username if message.user else "Unknown",
        user_avatar=message.user.avatar_url if message.user else None,
        content=message.content,
        file_name=message.file_name,
        file_path=message.file_path,
        file_size=message.file_size,
        file_type=message.file_type,
        version_id=message.version_id,
        version_number=message.version.version_number if message.version else None,
        version_title=message.version.title if message.version else None,
        reply_to_id=message.reply_to_id,
        reply_to_user_name=message.reply_to.user.username if message.reply_to and message.reply_to.user else None,
        reply_to_content=message.reply_to.content if message.reply_to else None,
        reply_to_file_name=message.reply_to.file_name if message.reply_to else None,
        reply_to_version_title=message.reply_to.version.title if message.reply_to and message.reply_to.version else None,
        reply_to_version_number=message.reply_to.version.version_number if message.reply_to and message.reply_to.version else None,
        edited_at=message.edited_at,
        deleted_by=message.deleted_by,
        reactions=message.reactions,
        created_at=message.created_at,
        user_badge_icon_svg=badge.icon_svg if badge else None,
        user_badge_ring_gradient=badge.avatar_ring_gradient if badge else None,
        user_badge_ring_effect=badge.avatar_ring_effect if badge else None,
        user_badge_name=badge.name if badge else None,
    )
