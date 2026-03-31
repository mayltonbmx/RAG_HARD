"""
stats.py — GET /api/stats — Estatisticas do indice Pinecone (requires authentication).
"""

from fastapi import APIRouter, HTTPException, Depends
from app.config import get_settings
from app.services.pinecone_db import get_stats
from app.services.ingest import scan_directory
from app.middleware.auth import azure_scheme

router = APIRouter(prefix="/api", tags=["stats"])

_deps = [Depends(azure_scheme)] if azure_scheme else []


@router.get("/stats", dependencies=_deps)
async def stats_endpoint():
    try:
        settings = get_settings()
        stats = get_stats()
        files = scan_directory()
        return {
            "total_vectors": stats.get("total_vector_count", 0),
            "dimension": stats.get("dimension", settings.embedding_dimensions),
            "index_fullness": stats.get("index_fullness", 0),
            "model": settings.embedding_model,
            "total_files": len(files),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
