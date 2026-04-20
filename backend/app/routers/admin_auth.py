"""
admin_auth.py — Login genérico para admin (usuário/senha via .env + JWT).
"""

import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin-auth"])

TOKEN_EXPIRY_HOURS = 24


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_in: int  # seconds
    role: str


@router.post("/login", response_model=LoginResponse)
async def admin_login(req: LoginRequest):
    """Autentica admin com credenciais do .env e retorna JWT."""
    settings = get_settings()

    if not settings.admin_user or not settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin login não configurado. Defina ADMIN_USER e ADMIN_PASSWORD no .env",
        )

    if req.username != settings.admin_user or req.password != settings.admin_password:
        logger.warning(f"Admin login failed for user: {req.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos.",
        )

    # Gera JWT
    now = datetime.now(timezone.utc)
    payload = {
        "sub": req.username,
        "role": "Admin",
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_EXPIRY_HOURS),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

    logger.info(f"Admin login successful: {req.username}")
    return LoginResponse(
        token=token,
        expires_in=TOKEN_EXPIRY_HOURS * 3600,
        role="Admin",
    )
