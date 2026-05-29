from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectAccessRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    requester_id: str
    requester_nickname: str = ""
    requester_username: str = ""
    requester_avatar: str | None = None
    status: str
    created_at: datetime


class AccessRequestAction(BaseModel):
    action: str  # "approve" | "deny"
