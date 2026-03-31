"""
search.py — POST /api/search — Busca semantica pura (requires authentication).
"""

import logging
from fastapi import APIRouter, HTTPException, Depends

from app.schemas.models import SearchRequest, SearchResponse
from app.services.embeddings import embed_query
from app.services.pinecone_db import search as pinecone_search
from app.middleware.auth import azure_scheme

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["search"])

_deps = [Depends(azure_scheme)] if azure_scheme else []


@router.post("/search", response_model=SearchResponse, dependencies=_deps)
async def search_endpoint(req: SearchRequest):
    try:
        query_vector = embed_query(req.query)

        filter_dict = None
        if req.file_type and req.file_type != "all":
            filter_dict = {"file_type": {"$eq": req.file_type}}

        results = pinecone_search(
            query_vector=query_vector,
            top_k=req.top_k,
            filter_dict=filter_dict,
        )

        return SearchResponse(results=results, query=req.query)
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
