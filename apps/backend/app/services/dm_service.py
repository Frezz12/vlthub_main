import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.dm import DirectMessage, DirectMessageRoom
from app.models.badge import UserBadge
from app.models.user import User
from app.schemas.dm import DirectMessageHistoryOut, DirectMessageOut, DirectMessageRoomOut

CHAT_FILE_MAX_SIZE = 100 * 1024 * 1024


def _get_active_badge(user):
    if not user or not user.badges:
        return None
    for ub in user.badges:
        if ub.is_active and ub.badge:
            return ub.badge
    return None


async def get_or_create_room(session: AsyncSession, user1_id: str, user2_id: str) -> DirectMessageRoom:
    result = await session.execute(
        select(DirectMessageRoom)
        .options(
            selectinload(DirectMessageRoom.user1).selectinload(User.badges).selectinload(UserBadge.badge),
            selectinload(DirectMessageRoom.user2).selectinload(User.badges).selectinload(UserBadge.badge),
        )
        .where(
            ((DirectMessageRoom.user1_id == user1_id) & (DirectMessageRoom.user2_id == user2_id)) |
            ((DirectMessageRoom.user1_id == user2_id) & (DirectMessageRoom.user2_id == user1_id))
        )
    )
    room = result.scalar_one_or_none()
    if room:
        return room
    room = DirectMessageRoom(user1_id=user1_id, user2_id=user2_id)
    session.add(room)
    await session.commit()
    result = await session.execute(
        select(DirectMessageRoom)
        .options(
            selectinload(DirectMessageRoom.user1).selectinload(User.badges).selectinload(UserBadge.badge),
            selectinload(DirectMessageRoom.user2).selectinload(User.badges).selectinload(UserBadge.badge),
        )
        .where(DirectMessageRoom.id == room.id)
    )
    return result.scalar_one()


async def create_message(
    session: AsyncSession, room_id: str, sender_id: str, content: str, reply_to_id: str | None = None
) -> DirectMessage:
    room_result = await session.execute(
        select(DirectMessageRoom).where(DirectMessageRoom.id == room_id)
    )
    room = room_result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    if sender_id not in (room.user1_id, room.user2_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    message = DirectMessage(room_id=room_id, sender_id=sender_id, content=content, reply_to_id=reply_to_id)
    session.add(message)
    room.last_message_at = datetime.now(timezone.utc)
    room.last_message_content = content if content.strip() else 'Файл'
    await session.commit()
    return await _load_message(session, message.id)


async def _load_message(session: AsyncSession, message_id: str) -> DirectMessage:
    result = await session.execute(
        select(DirectMessage)
        .options(
            selectinload(DirectMessage.sender).selectinload(User.badges).selectinload(UserBadge.badge),
            selectinload(DirectMessage.reply_to).selectinload(DirectMessage.sender).selectinload(User.badges).selectinload(UserBadge.badge),
        )
        .where(DirectMessage.id == message_id)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return msg


def message_to_out(message: DirectMessage, current_user_id: str | None = None) -> DirectMessageOut:
    badge = _get_active_badge(message.sender)
    return DirectMessageOut(
        id=message.id,
        room_id=message.room_id,
        sender_id=message.sender_id,
        sender_name=message.sender.nickname if message.sender else "Unknown",
        sender_avatar=message.sender.avatar_url if message.sender else None,
        content=message.content,
        file_name=message.file_name,
        file_path=message.file_path,
        file_size=message.file_size,
        file_type=message.file_type,
        reply_to_id=message.reply_to_id,
        reply_to_sender_name=message.reply_to.sender.nickname if message.reply_to and message.reply_to.sender else None,
        reply_to_content=message.reply_to.content if message.reply_to else None,
        edited_at=message.edited_at,
        deleted_by=message.deleted_by,
        reactions=message.reactions,
        read_at=message.read_at,
        created_at=message.created_at,
        sender_badge_icon_svg=badge.icon_svg if badge else None,
        sender_badge_ring_gradient=badge.avatar_ring_gradient if badge else None,
        sender_badge_ring_effect=badge.avatar_ring_effect if badge else None,
        sender_badge_name=badge.name if badge else None,
    )


async def get_messages(
    session: AsyncSession, room_id: str, user_id: str, limit: int = 50, offset: int = 0
) -> tuple[list[DirectMessage], int]:
    room_result = await session.execute(
        select(DirectMessageRoom).where(DirectMessageRoom.id == room_id)
    )
    room = room_result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    if user_id not in (room.user1_id, room.user2_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    total_result = await session.execute(
        select(func.count(DirectMessage.id)).where(DirectMessage.room_id == room_id)
    )
    total = total_result.scalar() or 0

    result = await session.execute(
        select(DirectMessage)
        .options(
            selectinload(DirectMessage.sender).selectinload(User.badges).selectinload(UserBadge.badge),
            selectinload(DirectMessage.reply_to).selectinload(DirectMessage.sender).selectinload(User.badges).selectinload(UserBadge.badge),
        )
        .where(DirectMessage.room_id == room_id)
        .order_by(DirectMessage.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))
    messages = [m for m in messages if not (m.deleted_by and user_id in m.deleted_by)]
    total = len(messages) + offset
    return messages, total


async def _count_unread(session: AsyncSession, room_id: str, user_id: str) -> int:
    all_msgs = await session.execute(
        select(DirectMessage.id, DirectMessage.deleted_by)
        .where(
            DirectMessage.room_id == room_id,
            DirectMessage.sender_id != user_id,
            DirectMessage.read_at.is_(None),
        )
    )
    count = 0
    for mid, deleted_by in all_msgs:
        if not deleted_by or user_id not in deleted_by:
            count += 1
    return count


async def mark_room_read(session: AsyncSession, room_id: str, user_id: str) -> None:
    now = datetime.now(timezone.utc)
    await session.execute(
        DirectMessage.__table__.update()
        .where(
            DirectMessage.room_id == room_id,
            DirectMessage.sender_id != user_id,
            DirectMessage.read_at.is_(None),
        )
        .values(read_at=now)
    )
    await session.commit()


async def get_user_rooms(
    session: AsyncSession, user_id: str
) -> list[DirectMessageRoom]:
    result = await session.execute(
        select(DirectMessageRoom)
        .options(
            selectinload(DirectMessageRoom.user1).selectinload(User.badges).selectinload(UserBadge.badge),
            selectinload(DirectMessageRoom.user2).selectinload(User.badges).selectinload(UserBadge.badge),
        )
        .where(
            (DirectMessageRoom.user1_id == user_id) | (DirectMessageRoom.user2_id == user_id)
        )
        .order_by(DirectMessageRoom.last_message_at.desc().nullslast(), DirectMessageRoom.created_at.desc())
    )
    rooms = list(result.scalars().all())
    return [r for r in rooms if not (r.deleted_by and user_id in r.deleted_by)]


async def update_message(
    session: AsyncSession, message_id: str, user_id: str, content: str
) -> DirectMessage:
    result = await session.execute(
        select(DirectMessage).where(DirectMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if message.sender_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit another user's message")
    message.content = content
    message.edited_at = datetime.now(timezone.utc)
    await session.commit()
    return await _load_message(session, message.id)


async def delete_message(
    session: AsyncSession, message_id: str, user_id: str, scope: str = "all"
) -> None:
    result = await session.execute(
        select(DirectMessage).where(DirectMessage.id == message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    if scope == "all":
        if message.sender_id != user_id:
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
) -> DirectMessage:
    result = await session.execute(
        select(DirectMessage)
        .options(
            selectinload(DirectMessage.sender).selectinload(User.badges).selectinload(UserBadge.badge),
        )
        .where(DirectMessage.id == message_id)
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


async def create_file_message(
    session: AsyncSession, room_id: str, sender_id: str, content: str, file_name: str, file_data: bytes, reply_to_id: str | None = None
) -> DirectMessage:
    file_size = len(file_data)

    message_id = str(uuid.uuid4())
    storage_rel = f"dm/{room_id}/{message_id}/{file_name}"
    storage_path = (Path(settings.upload_dir).resolve() / storage_rel)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_bytes(file_data)

    room_result = await session.execute(
        select(DirectMessageRoom).where(DirectMessageRoom.id == room_id)
    )
    room = room_result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    if sender_id not in (room.user1_id, room.user2_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    content = content if content.strip() else ""

    message = DirectMessage(
        id=message_id,
        room_id=room_id,
        sender_id=sender_id,
        content=content,
        file_name=file_name,
        file_path=f"/uploads/{storage_rel}",
        file_size=file_size,
        file_type=file_name.rsplit(".", 1)[-1] if "." in file_name else "",
        reply_to_id=reply_to_id,
    )
    session.add(message)
    room.last_message_at = datetime.now(timezone.utc)
    room.last_message_content = content if content.strip() else 'Файл'
    await session.commit()
    return await _load_message(session, message.id)


def _delete_room_files(room_id: str) -> None:
    room_dir = (Path(settings.upload_dir).resolve() / "dm" / room_id)
    if room_dir.exists():
        shutil.rmtree(room_dir, ignore_errors=True)


async def delete_room(
    session: AsyncSession, room_id: str, user_id: str, scope: str = "all"
) -> None:
    result = await session.execute(
        select(DirectMessageRoom)
        .options(selectinload(DirectMessageRoom.messages))
        .where(DirectMessageRoom.id == room_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    if user_id not in (room.user1_id, room.user2_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    if scope == "all":
        _delete_room_files(room_id)
        await session.delete(room)
    else:
        deleted_by = room.deleted_by or []
        if user_id not in deleted_by:
            deleted_by.append(user_id)
        room.deleted_by = deleted_by
        for msg in room.messages:
            d = msg.deleted_by or []
            if user_id not in d:
                d.append(user_id)
            msg.deleted_by = d
    await session.commit()


async def room_to_out(room: DirectMessageRoom, current_user_id: str, session: AsyncSession | None = None) -> DirectMessageRoomOut:
    other_user = room.user2 if room.user1_id == current_user_id else room.user1
    badge = _get_active_badge(other_user)
    unread = 0
    if session:
        unread = await _count_unread(session, room.id, current_user_id)
    return DirectMessageRoomOut(
        id=room.id,
        user1_id=room.user1_id,
        user2_id=room.user2_id,
        other_user_id=other_user.id,
        other_user_name=other_user.nickname,
        other_user_username=other_user.username,
        other_user_avatar=other_user.avatar_url,
        last_message_at=room.last_message_at,
        last_message_content=room.last_message_content,
        unread_count=unread,
        created_at=room.created_at,
        other_user_last_seen_at=other_user.last_seen_at,
        other_user_badge_icon_svg=badge.icon_svg if badge else None,
        other_user_badge_ring_gradient=badge.avatar_ring_gradient if badge else None,
        other_user_badge_ring_effect=badge.avatar_ring_effect if badge else None,
        other_user_badge_name=badge.name if badge else None,
    )
