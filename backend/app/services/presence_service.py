"""Presence assignment.

A Presence is the in-séance identity of a Seeker. Sigils are generated
randomly and must be unique within the seance — we retry a small number
of times before giving up, which is overwhelmingly enough for the size of
the sigil namespace (~30 * 32 plus the and/number variants).
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.sigils import generate_sigil
from app.models.presence import Presence, PresenceRole

_MAX_SIGIL_ATTEMPTS = 8


def assign_presence(seeker_id: int, seance_id: int, role: PresenceRole, db: Session) -> Presence:
    """Create a Presence with a fresh, unique-within-seance sigil.

    The caller must commit the surrounding transaction.
    """

    last_error: IntegrityError | None = None
    for _ in range(_MAX_SIGIL_ATTEMPTS):
        sigil = generate_sigil()
        presence = Presence(
            seeker_id=seeker_id,
            seance_id=seance_id,
            sigil=sigil,
            role=role,
        )
        db.add(presence)
        try:
            db.flush()
            return presence
        except IntegrityError as exc:
            db.rollback()
            last_error = exc
            # Loop and retry with a different sigil.
            continue

    # Astronomically unlikely; surface a 503 rather than a 500.
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Could not assign a sigil; the veil is restless. Try again.",
    ) from last_error
