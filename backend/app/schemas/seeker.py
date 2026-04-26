from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class SeekerCreate(BaseModel):
    email: EmailStr
    password: str


class SeekerResponse(BaseModel):
    """Returned to the Seeker about themselves (e.g. after registration)."""

    id: int
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
