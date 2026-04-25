"""
main.py — FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.services.pinecone_db import init_index
from app.routers import health, chat, search, upload, files, stats, analytics, admin_auth, personas

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fontecerta")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    logger.info("=" * 50)
    logger.info("FonteCerta — Backend v3.0")
    logger.info("=" * 50)

    settings = get_settings()
    logger.info(f"Embedding model: {settings.embedding_model}")
    logger.info(f"Generation model: {settings.generation_model}")
    logger.info(f"CORS origins: {settings.cors_origins}")

    # Init Pinecone index
    init_index()

    # Init personas (cria defaults na primeira execução)
    from app.services.persona_service import init_personas
    init_personas()

    logger.info("Startup complete")

    yield  # App is running

    logger.info("Shutting down...")


# Create app
app = FastAPI(
    title="FonteCerta API",
    description="API de chat RAG com Gemini + Pinecone — Desenvolvido por Maylton Tavares",
    version="3.0.0",
    lifespan=lifespan,
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(upload.router)
app.include_router(files.router)
app.include_router(stats.router)
app.include_router(analytics.router)
app.include_router(admin_auth.router)
app.include_router(personas.router)


@app.get("/")
async def root():
    return {
        "name": "FonteCerta API",
        "version": "3.0.0",
        "auth": "JWT (admin)",
        "docs": "/docs",
    }
