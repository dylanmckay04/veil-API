from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_seeker, get_db
from app.core.limiter import limiter
from app.models.seeker import Seeker
from app.schemas.auth import LoginRequest, SocketTokenResponse, TokenResponse
from app.schemas.seeker import SeekerCreate, SeekerResponse
from app.services.auth_service import (
    issue_socket_token,
    login_seeker,
    register_seeker,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=SeekerResponse, status_code=201)
@limiter.limit("10/minute")
async def register(
    request: Request,
    payload: SeekerCreate,
    db: Session = Depends(get_db),
):
    return register_seeker(payload, db)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    access_token = login_seeker(payload.email, payload.password, db)
    return TokenResponse(access_token=access_token)


@router.post("/socket-token", response_model=SocketTokenResponse)
@limiter.limit("30/minute")
async def get_socket_token(
    request: Request,
    current_seeker: Seeker = Depends(get_current_seeker),
):
    token, jti = await issue_socket_token(current_seeker)
    return SocketTokenResponse(socket_token=token, jti=jti)
