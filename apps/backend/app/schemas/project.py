from datetime import datetime

from pydantic import BaseModel, field_validator

from app.schemas.user import UserBadgeBrief


PROJECT_STATUSES = ["in_progress", "completed", "on_hold", "dropped"]


class UserBrief(BaseModel):
    id: str
    nickname: str
    username: str
    avatar_url: str | None = None
    active_badge: UserBadgeBrief | None = None


class ProjectCreate(BaseModel):
    title: str
    artists: str | None = None
    sample_rate: int | None = None
    bpm: float | None = None
    key: str | None = None
    beatmaker: str | None = None
    status: str = "in_progress"
    description: str | None = None
    lyrics: str | None = None
    daw_type: str | None = None
    project_path: str | None = None
    tags: list[str] = []
    is_public: bool = False
    chat_enabled: bool = False


class ProjectUpdate(BaseModel):
    title: str | None = None
    artists: str | None = None
    sample_rate: int | None = None
    bpm: float | None = None
    key: str | None = None
    beatmaker: str | None = None
    status: str | None = None
    description: str | None = None
    lyrics: str | None = None
    cover_url: str | None = None
    daw_type: str | None = None
    project_path: str | None = None
    is_public: bool | None = None
    is_archived: bool | None = None
    is_favorite: bool | None = None
    tags: list[str] | None = None
    chat_enabled: bool | None = None


class CollaboratorOut(BaseModel):
    user_id: str
    nickname: str
    username: str
    avatar_url: str | None = None
    role: str
    status: str


class ProjectOut(BaseModel):
    id: str
    owner_id: str
    owner: UserBrief | None = None
    title: str
    artists: str | None = None
    sample_rate: int | None = None
    bpm: float | None
    key: str | None
    beatmaker: str | None = None
    status: str = "in_progress"
    description: str | None
    lyrics: str | None = None
    cover_url: str | None
    daw_type: str | None
    project_path: str | None = None
    my_project_path: str | None = None
    is_public: bool = False
    is_archived: bool
    is_favorite: bool = False
    chat_enabled: bool = False
    created_at: datetime
    updated_at: datetime
    tags: list[str] = []
    version_count: int = 0
    total_size: int = 0
    collaborators: list[CollaboratorOut] = []
    access_granted_at: datetime | None = None


class ProjectListOut(BaseModel):
    items: list[ProjectOut]
    total: int
    page: int
    limit: int


class CollaboratorInvite(BaseModel):
    email_or_username: str
    role: str = "editor"


class CollaboratorUpdate(BaseModel):
    role: str


class AccessUpdate(BaseModel):
    role: str


class UserProjectPathUpdate(BaseModel):
    project_path: str | None = None


class ShareLinkCreate(BaseModel):
    role: str = "editor"
    password: str | None = None
    expires_in_hours: int | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v != "editor":
            raise ValueError("Only 'editor' role is allowed for share links")
        return v


class ShareLinkOut(BaseModel):
    id: str
    token: str
    role: str
    expires_at: datetime | None
    created_at: datetime


class SharedProjectOut(BaseModel):
    id: str
    owner: UserBrief | None = None
    title: str
    artists: str | None = None
    sample_rate: int | None = None
    bpm: float | None
    key: str | None
    beatmaker: str | None = None
    status: str = "in_progress"
    description: str | None
    lyrics: str | None = None
    cover_url: str | None
    daw_type: str | None
    is_public: bool = False
    created_at: datetime
    updated_at: datetime
    tags: list[str] = []
    role: str = "viewer"
