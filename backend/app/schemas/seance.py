from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SeanceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=300)
    is_sealed: bool = False


class SeanceResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_sealed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SeanceDetail(SeanceResponse):
    presence_count: int
