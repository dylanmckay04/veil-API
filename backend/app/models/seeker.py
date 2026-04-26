from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Seeker(Base):
    """An account holder. The one who reaches across the veil.

    A Seeker authenticates and may enter many Seances; inside each Seance
    they manifest as a Presence with an ephemeral, randomly assigned sigil.
    The Seeker's identity itself is never exposed inside a Seance.
    """

    __tablename__ = "seekers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    warded_seances = relationship("Seance", back_populates="warden", foreign_keys="Seance.created_by")
    presences = relationship("Presence", back_populates="seeker", cascade="all, delete-orphan")
    whispers = relationship("Whisper", back_populates="seeker")
