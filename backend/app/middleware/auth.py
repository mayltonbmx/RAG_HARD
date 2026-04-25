"""
auth.py — Middleware de autenticação.

Suporta login admin genérico via JWT (user/password).
"""

import logging
from typing import Optional

import jwt as pyjwt
from fastapi import HTTPException, Request, status

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def _extract_admin_jwt(request: Request) -> Optional[dict]:
    """Extrai e valida JWT genérico do header Authorization."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    try:
        payload = pyjwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("role") == "Admin":
            return payload
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None

    return None


async def require_admin_any(request: Request):
    """Dependency: requer JWT admin genérico válido.

    Valida o token JWT do header Authorization.
    Se válido e com role Admin → OK
    Caso contrário → 401
    """
    admin_payload = _extract_admin_jwt(request)
    if admin_payload:
        return admin_payload

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Admin authentication required. Use /api/admin/login.",
    )
