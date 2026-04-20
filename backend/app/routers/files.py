"""
files.py — GET /api/files, DELETE /api/files/{filename}, PATCH /api/files/{filename}/standby
Gerenciamento de arquivos de treinamento (requires Admin).
"""

import os
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Query

from app.config import get_settings, SUPPORTED_EXTENSIONS
from app.services.ingest import scan_directory
from app.services.pinecone_db import delete_by_filename
from app.middleware.auth import require_admin_any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["files"])

_deps = [Depends(require_admin_any)]


@router.get("/files", dependencies=_deps)
async def list_files():
    try:
        files = scan_directory()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/files/{filename}/standby", dependencies=_deps)
async def toggle_standby(filename: str):
    """Desativa/ativa arquivo da base de treinamento (remove/reinsere vetores no Pinecone).

    Standby = remove vetores do Pinecone mas mantém arquivo no disco.
    """
    settings = get_settings()

    # Encontra o arquivo no disco
    file_path = _find_file(settings.data_dir, filename)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"Arquivo '{filename}' não encontrado.")

    # Remove vetores do Pinecone
    try:
        deleted = delete_by_filename(filename)
        logger.info(f"Standby: '{filename}' — {deleted} vetores removidos do Pinecone (arquivo mantido no disco)")
        return {
            "action": "standby",
            "filename": filename,
            "vectors_removed": deleted,
            "file_kept": True,
            "message": f"Arquivo desativado da base de treinamento. {deleted} vetores removidos.",
        }
    except Exception as e:
        logger.error(f"Standby error for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{filename}", dependencies=_deps)
async def delete_file(filename: str):
    """Exclui arquivo permanentemente (disco + vetores do Pinecone)."""
    settings = get_settings()

    # Encontra o arquivo no disco
    file_path = _find_file(settings.data_dir, filename)
    if not file_path:
        raise HTTPException(status_code=404, detail=f"Arquivo '{filename}' não encontrado.")

    # Remove vetores do Pinecone
    try:
        deleted = delete_by_filename(filename)
    except Exception as e:
        logger.error(f"Failed to delete vectors for {filename}: {e}")
        deleted = 0

    # Remove arquivo do disco
    try:
        os.remove(file_path)
        logger.info(f"Deleted: '{filename}' — arquivo removido do disco, {deleted} vetores removidos do Pinecone")
        return {
            "action": "delete",
            "filename": filename,
            "vectors_removed": deleted,
            "file_removed": True,
            "message": f"Arquivo excluído permanentemente. {deleted} vetores removidos.",
        }
    except Exception as e:
        logger.error(f"Delete file error for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _find_file(data_dir: str, filename: str) -> str | None:
    """Busca arquivo recursivamente no data_dir."""
    for root, _, files in os.walk(data_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None
