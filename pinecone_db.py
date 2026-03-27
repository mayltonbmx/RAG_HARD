"""
pinecone_db.py — Conexão e operações com o banco vetorial Pinecone.
"""

from pinecone import Pinecone, ServerlessSpec

from config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_CLOUD,
    PINECONE_REGION,
    EMBEDDING_DIMENSIONS,
)

# Cliente Pinecone (inicializado uma vez)
_pc = Pinecone(api_key=PINECONE_API_KEY)


def init_index() -> None:
    """
    Cria o índice Pinecone caso ele não exista.
    Usa spec Serverless com métrica cosine.
    """
    existing_indexes = [idx.name for idx in _pc.list_indexes()]

    if PINECONE_INDEX_NAME not in existing_indexes:
        _pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSIONS,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=PINECONE_CLOUD,
                region=PINECONE_REGION,
            ),
        )
        print(f"✅ Índice '{PINECONE_INDEX_NAME}' criado com sucesso.")
    else:
        print(f"ℹ️  Índice '{PINECONE_INDEX_NAME}' já existe.")


def _get_index():
    """Retorna referência ao índice Pinecone."""
    return _pc.Index(PINECONE_INDEX_NAME)


def upsert_vectors(
    vectors: list[dict],
    namespace: str = "",
    batch_size: int = 50,
) -> int:
    """
    Insere ou atualiza vetores no Pinecone.

    Args:
        vectors: Lista de dicts com campos:
            - id (str): ID único do vetor
            - values (list[float]): vetor de embedding
            - metadata (dict): metadados associados
        namespace: Namespace no Pinecone (default: "")
        batch_size: Tamanho do lote para upsert

    Returns:
        Número total de vetores inseridos.
    """
    index = _get_index()
    total = 0

    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]
        index.upsert(vectors=batch, namespace=namespace)
        total += len(batch)

    return total


def search(
    query_vector: list[float],
    top_k: int = 5,
    namespace: str = "",
    filter_dict: dict | None = None,
) -> list[dict]:
    """
    Busca os vetores mais similares no Pinecone.

    Args:
        query_vector: Vetor de embedding da consulta.
        top_k: Quantidade de resultados a retornar.
        namespace: Namespace para buscar.
        filter_dict: Filtro de metadados opcional.

    Returns:
        Lista de dicts com id, score e metadata.
    """
    index = _get_index()

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace,
        filter=filter_dict,
    )

    return [
        {
            "id": match.id,
            "score": match.score,
            "metadata": match.metadata,
        }
        for match in results.matches
    ]


def get_stats() -> dict:
    """Retorna estatísticas do índice Pinecone."""
    index = _get_index()
    return index.describe_index_stats()
