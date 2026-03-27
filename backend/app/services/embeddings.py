"""
embeddings.py — Geração de embeddings multimodais via Gemini Embedding 2.
"""

import logging
from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.gemini_api_key)
        logger.info("Gemini client initialized")
    return _client


def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    """Gera embedding de texto puro."""
    settings = get_settings()
    client = _get_client()

    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=settings.embedding_dimensions,
        ),
    )
    return result.embeddings[0].values


def embed_file(file_path: str, mime_type: str) -> list[float]:
    """Gera embedding de um arquivo (imagem, vídeo, áudio ou PDF)."""
    settings = get_settings()
    client = _get_client()

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    logger.info(f"Generating embedding for file: {file_path} ({mime_type})")

    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=types.Content(
            parts=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            ]
        ),
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=settings.embedding_dimensions,
        ),
    )
    return result.embeddings[0].values


def embed_query(text: str) -> list[float]:
    """Gera embedding otimizado para consultas de busca."""
    return embed_text(text, task_type="RETRIEVAL_QUERY")
