"""
pinecone_db.py — Conexão e operações com o banco vetorial Pinecone.
"""

import logging
from pinecone import Pinecone, ServerlessSpec

from app.config import get_settings

logger = logging.getLogger(__name__)

_pc: Pinecone | None = None


def _get_client() -> Pinecone:
    global _pc
    if _pc is None:
        settings = get_settings()
        _pc = Pinecone(api_key=settings.pinecone_api_key)
        logger.info("Pinecone client initialized")
    return _pc


def init_index() -> None:
    """Cria o índice caso não exista."""
    settings = get_settings()
    pc = _get_client()

    existing = [idx.name for idx in pc.list_indexes()]

    if settings.pinecone_index_name not in existing:
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.embedding_dimensions,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.pinecone_cloud,
                region=settings.pinecone_region,
            ),
        )
        logger.info(f"Index '{settings.pinecone_index_name}' created")
    else:
        logger.info(f"Index '{settings.pinecone_index_name}' already exists")


def _get_index():
    settings = get_settings()
    return _get_client().Index(settings.pinecone_index_name)


def upsert_vectors(vectors: list[dict], namespace: str = "", batch_size: int = 50) -> int:
    """Insere ou atualiza vetores."""
    index = _get_index()
    total = 0
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i: i + batch_size]
        index.upsert(vectors=batch, namespace=namespace)
        total += len(batch)
    logger.info(f"Upserted {total} vectors")
    return total


def search(query_vector: list[float], top_k: int = 5, namespace: str = "",
           filter_dict: dict | None = None) -> list[dict]:
    """Busca vetores mais similares."""
    index = _get_index()
    results = index.query(
        vector=query_vector, top_k=top_k,
        include_metadata=True, namespace=namespace, filter=filter_dict,
    )
    return [
        {"id": m.id, "score": m.score, "metadata": m.metadata}
        for m in results.matches
    ]


def get_stats() -> dict:
    """Estatísticas do índice."""
    return _get_index().describe_index_stats()
