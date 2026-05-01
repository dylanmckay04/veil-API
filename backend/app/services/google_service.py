import secrets

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.operator import Operator
from app.services.redis import redis_client

GOOGLE_STATE_TTL = 600
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


async def generate_google_login_url() -> dict:
    state = secrets.token_urlsafe(32)
    await redis_client.setex(f"google_oauth_state:{state}", GOOGLE_STATE_TTL, "valid")
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email",
        "state": state,
    }
    url = str(httpx.URL(GOOGLE_AUTHORIZE_URL).copy_with(params=params))
    return {"url": url, "state": state}


async def _validate_state(state: str) -> None:
    value = await redis_client.getdel(f"google_oauth_state:{state}")
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state.",
        )


async def _exchange_code_for_token(code: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth error: {data.get('error_description', data['error'])}",
        )
    return data["access_token"]


async def _fetch_google_user(google_token: str) -> tuple[str, str]:
    """Return (google_id_str, email)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_token}"},
        )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your Google account has no verified email address.",
        )
    email = data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your Google account has no verified email address.",
        )
    return str(data["sub"]), email


def _find_or_create_operator(google_id: str, email: str, db: Session) -> Operator:
    """Three-way lookup: by google_id → by email (link) → create new."""
    operator = db.query(Operator).filter(Operator.google_id == google_id).first()
    if operator:
        return operator

    operator = db.query(Operator).filter(Operator.email == email).first()
    if operator:
        operator.google_id = google_id
        db.commit()
        db.refresh(operator)
        return operator

    operator = Operator(email=email, hashed_password=None, google_id=google_id)
    db.add(operator)
    db.commit()
    db.refresh(operator)
    return operator


async def google_callback(code: str, state: str, db: Session) -> str:
    await _validate_state(state)
    google_token = await _exchange_code_for_token(code)
    google_id, email = await _fetch_google_user(google_token)
    operator = _find_or_create_operator(google_id, email, db)
    return create_access_token(data={"sub": str(operator.id)})
