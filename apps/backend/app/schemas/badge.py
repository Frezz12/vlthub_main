from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BadgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    icon_svg: str
    description: str | None = None
    avatar_ring_gradient: str | None = None
    avatar_ring_effect: str | None = None
    created_at: datetime


class UserBadgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    badge: BadgeOut
    is_active: bool


class BadgeCreate(BaseModel):
    name: str
    icon_svg: str
    description: str | None = None
    avatar_ring_gradient: str | None = None
    avatar_ring_effect: str | None = None


class BadgeUpdate(BaseModel):
    name: str | None = None
    icon_svg: str | None = None
    description: str | None = None
    avatar_ring_gradient: str | None = None
    avatar_ring_effect: str | None = None
