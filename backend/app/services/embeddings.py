"""
embeddings.py — Geração de embeddings multimodais via Gemini Embedding 2.
"""

import logging
import hashlib
from functools import lru_cache
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


def embed_texts_batch(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT",
                      batch_size: int = 20) -> list[list[float]]:
    """Gera embeddings para múltiplos textos em lote (batch).

    Reduz drasticamente o número de chamadas HTTP à API.
    Ex: 60 chunks → 3 chamadas (batch_size=20) em vez de 60.
    """
    settings = get_settings()
    client = _get_client()

    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(texts) + batch_size - 1) // batch_size

        logger.info(f"Batch embed {batch_num}/{total_batches}: {len(batch)} texts")

        result = client.models.embed_content(
            model=settings.embedding_model,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=settings.embedding_dimensions,
            ),
        )

        all_embeddings.extend([emb.values for emb in result.embeddings])

    logger.info(f"Batch embedding complete: {len(all_embeddings)} embeddings generated")
    return all_embeddings


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

@lru_cache(maxsize=256)
def _cached_embed_query(text: str) -> tuple[float, ...]:
    """Cached embedding para queries — evita chamadas repetidas à API."""
    values = embed_text(text, task_type="RETRIEVAL_QUERY")
    return tuple(values)  # lru_cache precisa de tipo hashável


def embed_query(text: str) -> list[float]:
    """Gera embedding otimizado para consultas de busca (com cache)."""
    cached = _cached_embed_query(text)
    return list(cached)


def get_cache_info() -> dict:
    """Retorna informações sobre o cache de embeddings."""
    info = _cached_embed_query.cache_info()
    return {
        "hits": info.hits,
        "misses": info.misses,
        "maxsize": info.maxsize,
        "currsize": info.currsize,
    }
