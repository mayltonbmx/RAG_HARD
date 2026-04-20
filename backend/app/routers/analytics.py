"""
analytics.py — GET /api/analytics — Dashboard de analytics (requires Admin).
"""

import logging
from fastapi import APIRouter, Depends, Query

from app.services.analytics import get_top_queries, get_usage_stats, rotate_logs
from app.middleware.auth import require_admin_any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Admin-only
_deps = [Depends(require_admin_any)]


@router.get("/top-queries", dependencies=_deps)
async def top_queries_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    days: int = Query(default=30, ge=1, le=365),
):
    """Retorna as N perguntas mais frequentes no período."""
    return {"queries": get_top_queries(limit=limit, days=days), "days": days}


@router.get("/stats", dependencies=_deps)
async def stats_endpoint(
    days: int = Query(default=30, ge=1, le=365),
):
    """Retorna métricas agregadas de uso."""
    return get_usage_stats(days=days)


@router.post("/rotate", dependencies=_deps)
async def rotate_endpoint():
    """Roda a rotação de logs (remove > 90 dias)."""
    removed = rotate_logs()
    return {"removed": removed, "retention_days": 90}
