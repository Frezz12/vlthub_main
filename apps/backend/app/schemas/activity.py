from pydantic import BaseModel


class ActivityDay(BaseModel):
    date: str
    count: int


class ActivityResponse(BaseModel):
    items: list[ActivityDay]
    total: int
