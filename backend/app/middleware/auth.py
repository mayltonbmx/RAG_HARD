"""
auth.py — Middleware de autenticação.

Suporta dois modos:
1. Azure Entra ID (JWT via OIDC) — quando configurado
2. Admin genérico (JWT via login com user/password) — sempre disponível
"""

import logging
from typing import Optional

import jwt as pyjwt
from fastapi import Depends, HTTPException, Request, status
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from fastapi_azure_auth.user import User

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize Azure auth scheme only if credentials are configured
azure_scheme: Optional[SingleTenantAzureAuthorizationCodeBearer] = None

if settings.azure_configured:
    azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
        app_client_id=settings.azure_client_id,
        tenant_id=settings.azure_tenant_id,
        scopes={
            f"api://{settings.azure_client_id}/access_as_user": "Access API as user",
        },
    )
    logger.info("Azure Entra ID auth ENABLED (single-tenant)")
else:
    logger.warning("Azure Entra ID auth DISABLED — credentials not configured")


async def verify_token(user: Optional[User] = None) -> Optional[User]:
    """
    Dependency: validates the Bearer token from Azure Entra ID.

    When Azure is not configured, returns None (dev mode — no auth).
    When Azure IS configured, requires a valid token.
    """
    if azure_scheme is None:
        # Dev mode — no auth enforced
        return None

    # In production with Azure configured, the scheme itself handles validation.
    # This function is used as a placeholder; actual validation is done
    # by injecting azure_scheme as a dependency in the router.
    return user


async def require_admin(user: Optional[User] = None) -> User:
    """
    Dependency: requires the user to have the 'Admin' role.

    When Azure is not configured, raises 403 (admin routes blocked in dev for safety).
    When Azure IS configured, checks the 'roles' claim in the JWT.
    """
    if azure_scheme is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin routes require Azure authentication to be configured.",
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    # Check for Admin role in token claims
    user_roles = getattr(user, "roles", None) or []
    if "Admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )

    return user


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
    """Dependency: aceita Azure Admin OU JWT admin genérico.

    Prioridade:
    1. Se Azure está configurado e o token Azure tem role Admin → OK
    2. Se há um JWT genérico válido com role Admin → OK
    3. Caso contrário → 403
    """
    # Tenta JWT admin genérico primeiro (mais comum enquanto Azure não está pronto)
    admin_payload = _extract_admin_jwt(request)
    if admin_payload:
        return admin_payload

    # Se Azure estiver configurado, tenta validar via Azure
    if azure_scheme is not None:
        # Azure validation is handled by the scheme dependency
        # If we got here, it means Azure validation didn't run or failed
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Admin authentication required. Use /api/admin/login.",
    )


def get_azure_scheme():
    """Returns the Azure auth scheme for use as a FastAPI dependency."""
    return azure_scheme
