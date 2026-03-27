"""
health.py — Health check endpoint.
"""

from fastapi import APIRouter
from app.schemas.models import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        version="2.0.0",
        services={
            "gemini": "connected",
            "pinecone": "connected",
        },
    )
