"""
health.py — Health check endpoint com verificação real dos serviços.
"""

import time
import logging
from fastapi import APIRouter
from app.schemas.models import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["health"])


def _check_pinecone() -> dict:
    """Testa conexão real com Pinecone."""
    try:
        start = time.perf_counter()
        from app.services.pinecone_db import get_stats
        stats = get_stats()
        latency = round((time.perf_counter() - start) * 1000, 1)
        return {
            "status": "connected",
            "latency_ms": latency,
            "vectors": stats.get("total_vector_count", 0),
        }
    except Exception as e:
        logger.error(f"Pinecone health check failed: {e}")
        return {"status": "error", "error": str(e)}


def _check_gemini() -> dict:
    """Testa conexão real com Gemini API (embedding mínimo)."""
    try:
        start = time.perf_counter()
        from app.services.embeddings import embed_text
        embed_text("health check", task_type="RETRIEVAL_QUERY")
        latency = round((time.perf_counter() - start) * 1000, 1)
        return {"status": "connected", "latency_ms": latency}
    except Exception as e:
        logger.error(f"Gemini health check failed: {e}")
        return {"status": "error", "error": str(e)}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    pinecone = _check_pinecone()
    gemini = _check_gemini()

    all_ok = pinecone["status"] == "connected" and gemini["status"] == "connected"

    return HealthResponse(
        status="ok" if all_ok else "degraded",
        version="2.5.0",
        services={
            "pinecone": pinecone["status"],
            "gemini": gemini["status"],
        },
    )


@router.get("/health/detailed")
async def health_detailed():
    """Health check detalhado com latências (admin only em produção)."""
    pinecone = _check_pinecone()
    gemini = _check_gemini()

    all_ok = pinecone["status"] == "connected" and gemini["status"] == "connected"

    return {
        "status": "ok" if all_ok else "degraded",
        "version": "2.5.0",
        "services": {
            "pinecone": pinecone,
            "gemini": gemini,
        },
    }
