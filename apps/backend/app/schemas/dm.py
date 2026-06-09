from datetime import datetime

from pydantic import BaseModel


class DirectMessageCreate(BaseModel):
    content: str
    reply_to_id: str | None = None


class DirectMessageUpdate(BaseModel):
    content: str


class DirectMessageOut(BaseModel):
    id: str
    room_id: str
    sender_id: str
    sender_name: str
    sender_avatar: str | None = None
    content: str
    file_name: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    file_type: str | None = None
    reply_to_id: str | None = None
    reply_to_sender_name: str | None = None
    reply_to_content: str | None = None
    edited_at: datetime | None = None
    deleted_by: list[str] | None = None
    reactions: dict[str, list[str]] | None = None
    read_at: datetime | None = None
    created_at: datetime
    sender_badge_icon_svg: str | None = None
    sender_badge_ring_gradient: str | None = None
    sender_badge_ring_effect: str | None = None
    sender_badge_name: str | None = None

    model_config = {"from_attributes": True}


class DirectMessageRoomOut(BaseModel):
    id: str
    user1_id: str
    user2_id: str
    other_user_id: str
    other_user_name: str
    other_user_username: str
    other_user_avatar: str | None = None
    last_message_at: datetime | None = None
    last_message_content: str | None = None
    unread_count: int = 0
    created_at: datetime
    other_user_last_seen_at: datetime | None = None
    other_user_badge_icon_svg: str | None = None
    other_user_badge_ring_gradient: str | None = None
    other_user_badge_ring_effect: str | None = None
    other_user_badge_name: str | None = None

    model_config = {"from_attributes": True}


class DirectMessageHistoryOut(BaseModel):
    messages: list[DirectMessageOut]
    total: int
