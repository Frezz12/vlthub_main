from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ProjectActivityUserBrief(BaseModel):
    nickname: str
    username: str
    avatar_url: str | None = None


class ProjectActivityOut(BaseModel):
    id: str
    event_type: str
    created_at: datetime
    version_id: str | None = None
    details: dict[str, Any] | None = None
    user: ProjectActivityUserBrief


class ProjectActivityListOut(BaseModel):
    items: list[ProjectActivityOut]
    total: int
