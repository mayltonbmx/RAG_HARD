"""
stats.py — GET /api/stats — Estatisticas do indice Pinecone.
"""

from fastapi import APIRouter, HTTPException
from app.config import get_settings
from app.services.pinecone_db import get_stats
from app.services.ingest import scan_directory

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats")
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
