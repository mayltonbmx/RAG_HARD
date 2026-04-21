"""
files.py — GET /api/files, DELETE /api/files/{filename},
            DELETE /api/files/{filename}/history
Gerenciamento de arquivos de treinamento (requires Admin).

Abordagem 100% Pinecone-first: a lista de arquivos vem EXCLUSIVAMENTE do Pinecone
(fonte de verdade). Não depende de disco local nem GCS.
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Depends

from app.config import get_settings
from app.services.ingest import scan_directory
from app.services.pinecone_db import (
    delete_by_filename,
    delete_tombstone,
    get_indexed_files_metadata,
    insert_deletion_record,
)
from app.middleware.auth import require_admin_any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["files"])

_deps = [Depends(require_admin_any)]


@router.get("/files", dependencies=_deps)
async def list_files():
    """Lista arquivos — 100% Pinecone-first.

    Retorna arquivos ativos (com vetores) e histórico de exclusão (tombstones).
    Disco local é consultado apenas para enriquecer com path/modified quando
    disponível, mas NÃO é necessário para que os arquivos apareçam.
    """
    try:
        # Fonte ÚNICA de verdade: Pinecone (ativos + histórico)
        pinecone_files = get_indexed_files_metadata()

        # Enriquecimento OPCIONAL: disco local (pode falhar sem impacto)
        disk_by_name: dict[str, dict] = {}
        try:
            disk_files = scan_directory()
            disk_by_name = {f["name"]: f for f in disk_files}
        except Exception as e:
            logger.warning(f"Disk scan failed (not required): {e}")

        # Constrói lista final
        merged = []
        for pf in pinecone_files:
            disk_info = disk_by_name.get(pf["name"], {})
            entry = {
                "path": disk_info.get("path", ""),
                "name": pf["name"],
                "extension": pf["extension"],
                "mime_type": pf["mime_type"],
                "size_mb": pf["size_mb"],
                "modified": disk_info.get("modified", ""),
                "status": pf["status"],  # "active" ou "deleted"
                "vectors_count": pf["vectors_count"],
                "on_disk": pf["name"] in disk_by_name,
                "deleted_at": pf.get("deleted_at", ""),
            }
            merged.append(entry)

        return {"files": merged}
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{filename}", dependencies=_deps)
async def delete_file(filename: str):
    """Exclui arquivo da base de treinamento.

    Remove vetores do Pinecone e cria um tombstone para histórico.
    Remove arquivo do disco se existir.
    """
    # Busca metadados do arquivo ANTES de excluir (para o tombstone)
    all_files = get_indexed_files_metadata()
    file_meta = next((f for f in all_files if f["name"] == filename and f["status"] == "active"), None)

    # Remove vetores do Pinecone
    try:
        deleted = delete_by_filename(filename)
    except Exception as e:
        logger.error(f"Failed to delete vectors for {filename}: {e}")
        deleted = 0

    # Remove arquivo do disco (se existir)
    settings = get_settings()
    file_path = _find_file(settings.data_dir, filename)
    file_removed = False
    if file_path:
        try:
            os.remove(file_path)
            file_removed = True
        except Exception as e:
            logger.error(f"Delete file error for {filename}: {e}")

    if deleted == 0 and not file_removed:
        raise HTTPException(status_code=404, detail=f"Arquivo '{filename}' não encontrado.")

    # Cria tombstone para histórico de exclusão
    if file_meta and deleted > 0:
        try:
            insert_deletion_record(
                filename=filename,
                extension=file_meta.get("extension", ""),
                mime_type=file_meta.get("mime_type", ""),
                size_mb=file_meta.get("size_mb", 0),
                vectors_removed=deleted,
            )
        except Exception as e:
            logger.warning(f"Failed to insert tombstone for {filename}: {e}")

    logger.info(f"Deleted: '{filename}' — disco={'removido' if file_removed else 'não encontrado'}, {deleted} vetores removidos do Pinecone")
    return {
        "action": "delete",
        "filename": filename,
        "vectors_removed": deleted,
        "file_removed": file_removed,
        "message": f"Arquivo excluído. {deleted} vetores removidos." + (" Arquivo removido do disco." if file_removed else ""),
    }


@router.delete("/files/{filename}/history", dependencies=_deps)
async def clear_file_history(filename: str):
    """Remove o registro de exclusão (tombstone) do histórico."""
    try:
        removed = delete_tombstone(filename)
        if removed == 0:
            raise HTTPException(status_code=404, detail=f"Nenhum registro de exclusão encontrado para '{filename}'.")

        return {
            "action": "clear_history",
            "filename": filename,
            "tombstones_removed": removed,
            "message": f"Histórico de exclusão removido para '{filename}'.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear history error for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _find_file(data_dir: str, filename: str) -> str | None:
    """Busca arquivo recursivamente no data_dir."""
    for root, _, files in os.walk(data_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None
