"""
files.py — GET /api/files, DELETE /api/files/{filename},
            PATCH /api/files/{filename}/standby,
            PATCH /api/files/{filename}/activate
Gerenciamento de arquivos de treinamento (requires Admin).

Abordagem 100% Pinecone-first: a lista de arquivos vem EXCLUSIVAMENTE do Pinecone
(fonte de verdade). Não depende de disco local nem GCS.
Disco local é usado apenas como enriquecimento secundário (path, modified) quando
disponível, e para a funcionalidade de re-ativação (activate).
"""

import os
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends

from app.config import get_settings, SUPPORTED_EXTENSIONS
from app.services.ingest import scan_directory, ingest_pdf_chunked, ingest_file_whole
from app.services.pinecone_db import (
    delete_by_filename,
    get_indexed_files_metadata,
    upsert_vectors,
)
from app.middleware.auth import require_admin_any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["files"])

_deps = [Depends(require_admin_any)]


@router.get("/files", dependencies=_deps)
async def list_files():
    """Lista arquivos — 100% Pinecone-first.

    A lista vem inteiramente do Pinecone (fonte de verdade do que a IA conhece).
    Disco local é consultado apenas para enriquecer com path/modified quando
    disponível, mas NÃO é necessário para que os arquivos apareçam.

    Não depende de GCS, disco local, ou qualquer storage externo.
    """
    try:
        # Fonte ÚNICA de verdade: Pinecone
        pinecone_files = get_indexed_files_metadata()

        # Enriquecimento OPCIONAL: disco local (pode falhar sem impacto)
        disk_by_name: dict[str, dict] = {}
        try:
            disk_files = scan_directory()
            disk_by_name = {f["name"]: f for f in disk_files}
        except Exception as e:
            logger.warning(f"Disk scan failed (not required): {e}")

        # Constrói lista final — todos os arquivos vêm do Pinecone
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
                "status": "active",
                "vectors_count": pf["vectors_count"],
                "on_disk": pf["name"] in disk_by_name,
            }
            merged.append(entry)

        return {"files": merged}
    except Exception as e:
        logger.error(f"List files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/files/{filename}/standby", dependencies=_deps)
async def toggle_standby(filename: str):
    """Desativa arquivo da base de treinamento (remove vetores no Pinecone).

    Standby = remove vetores do Pinecone mas mantém arquivo no disco (se existir).
    """
    # Remove vetores do Pinecone
    try:
        deleted = delete_by_filename(filename)
        if deleted == 0:
            raise HTTPException(status_code=404, detail=f"Nenhum vetor encontrado para '{filename}' no Pinecone.")

        logger.info(f"Standby: '{filename}' — {deleted} vetores removidos do Pinecone")
        return {
            "action": "standby",
            "filename": filename,
            "vectors_removed": deleted,
            "message": f"Arquivo desativado da base de treinamento. {deleted} vetores removidos.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Standby error for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/files/{filename}/activate", dependencies=_deps)
async def activate_file(filename: str):
    """Reativa arquivo na base de treinamento (re-ingere vetores no Pinecone).

    Lê o arquivo do disco e executa o pipeline de ingestão completo.
    Requer que o arquivo exista no disco local.
    """
    settings = get_settings()

    # Encontra o arquivo no disco
    file_path = _find_file(settings.data_dir, filename)
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail=f"Arquivo '{filename}' não encontrado no disco. Para reativar, o arquivo precisa estar disponível localmente.",
        )

    ext = Path(file_path).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Tipo não suportado: {ext}")

    mime = SUPPORTED_EXTENSIONS[ext]
    size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)

    try:
        # Re-ingerir o arquivo
        if ext == ".pdf":
            vectors = ingest_pdf_chunked(file_path, filename, size_mb)
        else:
            vectors = ingest_file_whole(file_path, filename, ext, mime, size_mb)

        upsert_vectors(vectors)

        logger.info(f"Activate: '{filename}' — {len(vectors)} vetores inseridos no Pinecone")
        return {
            "action": "activate",
            "filename": filename,
            "vectors_inserted": len(vectors),
            "message": f"Arquivo reativado na base de treinamento. {len(vectors)} vetores inseridos.",
        }
    except Exception as e:
        logger.error(f"Activate error for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{filename}", dependencies=_deps)
async def delete_file(filename: str):
    """Exclui arquivo permanentemente (vetores do Pinecone + disco se existir)."""

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

    logger.info(f"Deleted: '{filename}' — disco={'removido' if file_removed else 'não encontrado'}, {deleted} vetores removidos do Pinecone")
    return {
        "action": "delete",
        "filename": filename,
        "vectors_removed": deleted,
        "file_removed": file_removed,
        "message": f"Arquivo excluído. {deleted} vetores removidos." + (" Arquivo removido do disco." if file_removed else ""),
    }


def _find_file(data_dir: str, filename: str) -> str | None:
    """Busca arquivo recursivamente no data_dir."""
    for root, _, files in os.walk(data_dir):
        if filename in files:
            return os.path.join(root, filename)
    return None
