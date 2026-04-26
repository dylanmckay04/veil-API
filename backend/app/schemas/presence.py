from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.presence import PresenceRole


class PresenceResponse(BaseModel):
    """A Presence as visible to other participants in the Seance.

    Deliberately omits seeker_id and email — the sigil is the only identity.
    """

    sigil: str
    role: PresenceRole
    entered_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OwnPresenceResponse(PresenceResponse):
    """Returned to the Seeker themselves when they enter a Seance, so
    their client knows which sigil belongs to them this round."""

    seance_id: int
