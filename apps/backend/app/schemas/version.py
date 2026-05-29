from datetime import datetime

from pydantic import BaseModel

from app.schemas.user import UserBadgeBrief


class VersionCreate(BaseModel):
    title: str | None = None
    description: str | None = None


class VersionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class VersionOut(BaseModel):
    id: str
    project_id: str
    version_number: int
    title: str | None
    description: str | None
    created_by: str | None
    file_size: int | None
    file_hash: str | None
    is_current: bool
    created_at: datetime
    updated_at: datetime
    file_count: int = 0
    audio_previews: list['AudioPreviewOut'] = []


class VersionListOut(BaseModel):
    items: list[VersionOut]
    total: int


class VersionFileOut(BaseModel):
    id: str
    version_id: str | None = None
    file_name: str
    file_size: int
    file_hash: str | None = None
    created_at: datetime | None = None


class AudioPreviewCreate(BaseModel):
    title: str | None = None


class AudioPreviewOut(BaseModel):
    id: str
    file_path: str
    title: str | None
    duration: float | None
    file_size: int | None
    created_at: datetime


class CommentCreate(BaseModel):
    text: str


class CommentOut(BaseModel):
    id: str
    user_id: str
    nickname: str
    username: str
    avatar_url: str | None = None
    active_badge: UserBadgeBrief | None = None
    text: str
    created_at: datetime


class CompareRequest(BaseModel):
    ver1: str
    ver2: str


class VersionTaskCreate(BaseModel):
    text: str


class VersionTaskUpdate(BaseModel):
    text: str | None = None
    is_done: bool | None = None
    position: int | None = None


class VersionTaskOut(BaseModel):
    id: str
    version_id: str
    text: str
    is_done: bool
    position: int
    created_at: datetime
