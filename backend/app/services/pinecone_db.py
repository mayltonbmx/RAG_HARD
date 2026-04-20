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
           filter_dict: dict | None = None, min_score: float = 0.35) -> list[dict]:
    """Busca vetores mais similares, filtrando resultados abaixo do score mínimo."""
    index = _get_index()
    results = index.query(
        vector=query_vector, top_k=top_k,
        include_metadata=True, namespace=namespace, filter=filter_dict,
    )
    matches = [
        {"id": m.id, "score": m.score, "metadata": m.metadata}
        for m in results.matches
        if m.score >= min_score
    ]
    if len(matches) < len(results.matches):
        logger.info(f"Score threshold {min_score}: {len(results.matches)} -> {len(matches)} results (filtered {len(results.matches) - len(matches)} low-score)")
    return matches


def get_stats() -> dict:
    """Estatísticas do índice."""
    return _get_index().describe_index_stats()


def delete_by_filename(filename: str, namespace: str = "") -> int:
    """Remove todos os vetores com metadata.filename == filename."""
    index = _get_index()

    # Busca IDs com o filename no metadata
    # Pinecone serverless requer list + delete
    try:
        # Tenta query com filter para encontrar IDs
        results = index.query(
            vector=[0.0] * get_settings().embedding_dimensions,
            top_k=10000,
            filter={"filename": {"$eq": filename}},
            include_metadata=False,
            namespace=namespace,
        )

        ids_to_delete = [m.id for m in results.matches]

        if ids_to_delete:
            # Deleta em batches de 100
            for i in range(0, len(ids_to_delete), 100):
                batch = ids_to_delete[i:i + 100]
                index.delete(ids=batch, namespace=namespace)

            logger.info(f"Deleted {len(ids_to_delete)} vectors for filename: {filename}")
        else:
            logger.info(f"No vectors found for filename: {filename}")

        return len(ids_to_delete)

    except Exception as e:
        logger.error(f"Delete by filename failed for {filename}: {e}")
        raise
