from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    SOCKET_TOKEN_EXPIRE_SECONDS,
    create_access_token,
    create_socket_token,
    hash_password,
    verify_password,
)
from app.models.seeker import Seeker
from app.schemas.seeker import SeekerCreate
from app.services.redis import redis_client


def register_seeker(payload: SeekerCreate, db: Session) -> Seeker:
    existing = db.query(Seeker).filter(Seeker.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    seeker = Seeker(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(seeker)
    db.commit()
    db.refresh(seeker)
    return seeker


def login_seeker(email: str, password: str, db: Session) -> str:
    """Validate credentials and return a signed access token."""
    seeker = db.query(Seeker).filter(Seeker.email == email).first()
    if not seeker or not verify_password(password, seeker.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    return create_access_token(data={"sub": str(seeker.id)})


async def issue_socket_token(seeker: Seeker) -> tuple[str, str]:
    """Mint a short-lived socket token and register its JTI in Redis.

    The JTI lives in Redis with a TTL slightly longer than the token itself
    so the WebSocket endpoint can verify the token has not yet been
    consumed (one-time-use). The endpoint should consume the JTI atomically
    (e.g. ``GETDEL``) when the connection is accepted.
    """
    token, jti = create_socket_token(data={"sub": str(seeker.id)})

    await redis_client.setex(
        f"socket_jti:{jti}",
        SOCKET_TOKEN_EXPIRE_SECONDS + 5,
        "valid",
    )

    return token, jti
