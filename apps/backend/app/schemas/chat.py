from datetime import datetime

from pydantic import BaseModel


class ChatMessageCreate(BaseModel):
    content: str
    reply_to_id: str | None = None


class ChatMessageUpdate(BaseModel):
    content: str


class ChatMessageOut(BaseModel):
    id: str
    room_id: str
    user_id: str
    user_name: str
    user_avatar: str | None = None
    content: str
    file_name: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    file_type: str | None = None
    version_id: str | None = None
    version_number: int | None = None
    version_title: str | None = None
    reply_to_id: str | None = None
    reply_to_user_name: str | None = None
    reply_to_content: str | None = None
    reply_to_file_name: str | None = None
    reply_to_version_title: str | None = None
    reply_to_version_number: int | None = None
    edited_at: datetime | None = None
    deleted_by: list[str] | None = None
    reactions: dict[str, list[str]] | None = None
    created_at: datetime
    user_badge_icon_svg: str | None = None
    user_badge_ring_gradient: str | None = None
    user_badge_ring_effect: str | None = None
    user_badge_name: str | None = None

    model_config = {"from_attributes": True}


class ChatRoomOut(BaseModel):
    id: str
    project_id: str
    created_at: datetime
    messages: list[ChatMessageOut] = []

    model_config = {"from_attributes": True}


class ChatHistoryOut(BaseModel):
    messages: list[ChatMessageOut]
    total: int


class ChatVersionAttach(BaseModel):
    content: str = ""
    version_id: str
    reply_to_id: str | None = None
