"""
auth.py — Azure Entra ID (OpenID Connect) authentication middleware.

Uses fastapi-azure-auth to validate JWT tokens from Microsoft Entra ID.
When Azure is not configured (no credentials), auth is bypassed for development.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
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


def get_azure_scheme():
    """Returns the Azure auth scheme for use as a FastAPI dependency."""
    return azure_scheme
