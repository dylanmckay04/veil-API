from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WhisperCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class WhisperResponse(BaseModel):
    """A whisper as it should be displayed in the séance.

    The originating Seeker is intentionally not exposed here; only the
    sigil that was assigned at the moment the whisper was uttered.
    """

    id: int
    seance_id: int
    sigil: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WhisperPage(BaseModel):
    """Cursor-style pagination envelope. `next_before_id` is the value to
    pass as `before_id` on the next request to keep walking backwards in
    time; null means you've reached the very first whisper."""

    items: list[WhisperResponse]
    next_before_id: int | None = None
