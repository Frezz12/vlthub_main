from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr


class SocialLinkOut(BaseModel):
    platform: str
    url: str


class UserBadgeBrief(BaseModel):
    id: str
    name: str
    icon_svg: str
    description: str | None = None
    avatar_ring_gradient: str | None = None
    avatar_ring_effect: str | None = None
    is_active: bool = False


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    nickname: str
    username: str
    bio: str | None
    avatar_url: str | None
    cover_url: str | None = None
    is_public: bool
    is_email_confirmed: bool
    created_at: datetime
    social_links: list[SocialLinkOut] = []
    settings: dict[str, Any] = {}
    is_admin: bool = False
    storage_limit: int = 5_368_709_120
    storage_used: int = 0
    badges: list[UserBadgeBrief] = []
    active_badge: UserBadgeBrief | None = None


class UserAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    nickname: str
    username: str
    avatar_url: str | None
    is_admin: bool
    storage_limit: int
    storage_used: int
    created_at: datetime
    active_badge: UserBadgeBrief | None = None


class SetStorageLimit(BaseModel):
    storage_limit_gb: int


class StorageSummaryOut(BaseModel):
    total_users: int
    total_used: int
    total_limit: int


class UserSettingsUpdate(BaseModel):
    settings: dict[str, Any]


class UserUpdate(BaseModel):
    nickname: str | None = None
    username: str | None = None
    bio: str | None = None
    cover_url: str | None = None
    is_public: bool | None = None


class SocialLinkUpdate(BaseModel):
    platform: str
    url: str


class NotificationSettingsUpdate(BaseModel):
    notification_type: str
    email_enabled: bool | None = None
    in_app_enabled: bool | None = None


class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nickname: str
    username: str
    bio: str | None
    avatar_url: str | None
    cover_url: str | None = None
    is_public: bool
    created_at: datetime
    social_links: list[SocialLinkOut] = []
    project_count: int = 0
    version_count: int = 0
    collaboration_count: int = 0
    follower_count: int = 0
    following_count: int = 0
    is_following: bool = False
    projects: list["ProjectOut"] = []
    active_badge: UserBadgeBrief | None = None


class UserSearchResult(BaseModel):
    id: str
    nickname: str
    username: str
    avatar_url: str | None
    is_following: bool = False
    active_badge: UserBadgeBrief | None = None


class FollowOut(BaseModel):
    id: str
    nickname: str
    username: str
    avatar_url: str | None
    active_badge: UserBadgeBrief | None = None
    followed_at: datetime


from app.schemas.project import ProjectOut  # noqa: E402, F811
