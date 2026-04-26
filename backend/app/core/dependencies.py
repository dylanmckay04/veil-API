from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import SessionLocal
from app.models.seeker import Seeker

http_bearer = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_seeker(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> Seeker:
    """Resolve the bearer token to a Seeker or raise 401.

    Note: ``decode_access_token`` returns ``None`` for any failure — including
    expired, malformed, wrong-typed, or missing tokens — so we must guard
    against that before reading ``payload`` (this used to raise 500).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    sub = payload.get("sub")
    if sub is None:
        raise credentials_exception

    # ``sub`` is stored as str(int) — coerce defensively.
    try:
        seeker_id = int(sub)
    except (TypeError, ValueError):
        raise credentials_exception

    seeker = db.query(Seeker).filter(Seeker.id == seeker_id).first()
    if seeker is None:
        raise credentials_exception

    return seeker
