"""
pinecone_db.py — Conexão e operações com o banco vetorial Pinecone.
"""

import hashlib
import logging
from datetime import datetime, timezone

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
    """Remove todos os vetores com metadata.filename == filename (exceto tombstones)."""
    index = _get_index()

    try:
        results = index.query(
            vector=[0.0] * get_settings().embedding_dimensions,
            top_k=10000,
            filter={"filename": {"$eq": filename}},
            include_metadata=True,
            namespace=namespace,
        )

        # Filtra IDs que NÃO são tombstones (não queremos deletar o histórico)
        ids_to_delete = [
            m.id for m in results.matches
            if not m.metadata.get("is_tombstone", False)
        ]

        if ids_to_delete:
            for i in range(0, len(ids_to_delete), 100):
                batch = ids_to_delete[i:i + 100]
                index.delete(ids=batch, namespace=namespace)

            logger.info(f"Deleted {len(ids_to_delete)} vectors for filename: {filename}")
        else:
            logger.info(f"No active vectors found for filename: {filename}")

        return len(ids_to_delete)

    except Exception as e:
        logger.error(f"Delete by filename failed for {filename}: {e}")
        raise


def insert_deletion_record(filename: str, extension: str, mime_type: str,
                           size_mb: float, vectors_removed: int,
                           namespace: str = "") -> None:
    """Insere um vetor tombstone no Pinecone para registrar a exclusão de um arquivo.

    O tombstone usa um vetor zero e metadados especiais para que:
    - Não apareça em buscas de RAG (score ~0)
    - Seja identificável como registro de exclusão (is_tombstone=True)
    - Contenha info do arquivo original para histórico
    """
    index = _get_index()
    dim = get_settings().embedding_dimensions

    tombstone_id = f"tombstone_{hashlib.md5(f'{filename}_{datetime.now(timezone.utc).isoformat()}'.encode()).hexdigest()}"

    tombstone = {
        "id": tombstone_id,
        "values": [1e-7] * dim,  # epsilon, não zero (cosseno de zero é indefinido)
        "metadata": {
            "filename": filename,
            "file_type": extension,
            "mime_type": mime_type,
            "size_mb": size_mb,
            "is_tombstone": True,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "vectors_removed": vectors_removed,
            "content_type": "deletion_record",
            "text": f"[Registro de exclusão: {filename}]",
        },
    }

    index.upsert(vectors=[tombstone], namespace=namespace)
    logger.info(f"Tombstone inserted for deleted file: {filename}")


def delete_tombstone(filename: str, namespace: str = "") -> int:
    """Remove o tombstone de um arquivo do histórico de exclusão."""
    index = _get_index()

    try:
        results = index.query(
            vector=[0.0] * get_settings().embedding_dimensions,
            top_k=10000,
            filter={"filename": {"$eq": filename}, "is_tombstone": {"$eq": True}},
            include_metadata=False,
            namespace=namespace,
        )

        ids = [m.id for m in results.matches]
        if ids:
            for i in range(0, len(ids), 100):
                index.delete(ids=ids[i:i + 100], namespace=namespace)
            logger.info(f"Removed {len(ids)} tombstones for: {filename}")

        return len(ids)

    except Exception as e:
        logger.error(f"Failed to delete tombstone for {filename}: {e}")
        raise


def get_indexed_filenames(namespace: str = "") -> set[str]:
    """Consulta o Pinecone para descobrir quais filenames possuem vetores ativos.

    Retorna um set com os nomes dos arquivos que têm pelo menos 1 vetor indexado.
    """
    files_meta = get_indexed_files_metadata(namespace)
    return {f["name"] for f in files_meta if f["status"] == "active"}


def get_indexed_files_metadata(namespace: str = "") -> list[dict]:
    """Consulta o Pinecone e retorna inventário completo: arquivos ativos + histórico de exclusão.

    Retorna dois tipos de registros:
    - status="active": arquivos com vetores ativos (a IA conhece)
    - status="deleted": tombstones de arquivos excluídos (histórico)
    """
    index = _get_index()
    settings = get_settings()
    dim = settings.embedding_dimensions

    active_files: dict[str, dict] = {}
    deleted_files: list[dict] = []

    try:
        results = index.query(
            vector=[0.0] * dim,
            top_k=10000,
            include_metadata=True,
            namespace=namespace,
        )

        for match in results.matches:
            meta = match.metadata
            if not meta or "filename" not in meta:
                continue

            fname = meta["filename"]

            # Tombstone = registro de exclusão
            if meta.get("is_tombstone", False):
                deleted_files.append({
                    "name": fname,
                    "extension": meta.get("file_type", ""),
                    "mime_type": meta.get("mime_type", ""),
                    "size_mb": meta.get("size_mb", 0),
                    "vectors_count": meta.get("vectors_removed", 0),
                    "status": "deleted",
                    "deleted_at": meta.get("deleted_at", ""),
                })
                continue

            # Arquivo ativo
            if fname not in active_files:
                active_files[fname] = {
                    "name": fname,
                    "extension": meta.get("file_type", ""),
                    "mime_type": meta.get("mime_type", ""),
                    "size_mb": meta.get("size_mb", 0),
                    "file_type": meta.get("file_type", ""),
                    "vectors_count": 0,
                    "status": "active",
                    "source": "pinecone",
                    "allowed_personas": meta.get("allowed_personas", []),
                }

            active_files[fname]["vectors_count"] += 1
            # Mantém allowed_personas do primeiro vetor com a info
            if meta.get("allowed_personas") and not active_files[fname]["allowed_personas"]:
                active_files[fname]["allowed_personas"] = meta["allowed_personas"]

        active = sorted(active_files.values(), key=lambda f: f["name"])
        deleted = sorted(deleted_files, key=lambda f: f.get("deleted_at", ""), reverse=True)

        logger.info(f"Pinecone inventory: {len(active)} active, {len(deleted)} deleted, {sum(f['vectors_count'] for f in active)} total vectors")
        return active + deleted

    except Exception as e:
        logger.error(f"Failed to get indexed files metadata: {e}")
        return []


def update_file_personas(filename: str, persona_ids: list[str], namespace: str = "") -> int:
    """Atualiza o campo allowed_personas em todos os vetores de um arquivo.

    Args:
        filename: Nome do arquivo
        persona_ids: Lista de IDs de personas que podem acessar este arquivo.
                     Lista vazia = acessível por todos (sem restrição).
    """
    index = _get_index()
    settings = get_settings()

    try:
        results = index.query(
            vector=[0.0] * settings.embedding_dimensions,
            top_k=10000,
            filter={"filename": {"$eq": filename}, "is_tombstone": {"$ne": True}},
            include_metadata=True,
            namespace=namespace,
        )

        if not results.matches:
            logger.warning(f"No vectors found for file: {filename}")
            return 0

        updated = 0
        for match in results.matches:
            meta = match.metadata or {}
            meta["allowed_personas"] = persona_ids
            index.update(id=match.id, set_metadata=meta, namespace=namespace)
            updated += 1

        logger.info(f"Updated allowed_personas for '{filename}': {len(persona_ids)} personas, {updated} vectors")
        return updated

    except Exception as e:
        logger.error(f"Failed to update personas for {filename}: {e}")
        raise
