"""
upload.py — POST /api/upload — Upload e ingestao de arquivos (requires Admin role).
"""

import os
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends

from app.config import get_settings, SUPPORTED_EXTENSIONS
from app.services.ingest import ingest_pdf_chunked, ingest_file_whole, generate_id
from app.services.pinecone_db import upsert_vectors
from app.middleware.auth import azure_scheme, require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["upload"])

# Admin-only: require both authentication and Admin role
_deps = [Depends(azure_scheme), Depends(require_admin)] if azure_scheme else [Depends(require_admin)]


@router.post("/upload", dependencies=_deps)
async def upload_files(files: list[UploadFile] = File(...)):
    settings = get_settings()
    results = {"success": [], "errors": []}

    for file in files:
        if not file.filename:
            continue

        filename = file.filename
        ext = Path(filename).suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            results["errors"].append({"file": filename, "error": f"Tipo nao suportado: {ext}"})
            continue

        # Define subpasta
        subfolder = "documentos" if ext == ".pdf" else \
                    "imagens" if ext in (".png", ".jpg", ".jpeg", ".webp") else \
                    "videos" if ext == ".mp4" else "documentos"

        save_dir = os.path.join(settings.data_dir, subfolder)
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)

        # Salva arquivo
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)

        try:
            size_mb = round(len(content) / (1024 * 1024), 2)
            mime = SUPPORTED_EXTENSIONS[ext]

            if ext == ".pdf":
                vectors = ingest_pdf_chunked(filepath, filename, size_mb)
            else:
                vectors = ingest_file_whole(filepath, filename, ext, mime, size_mb)

            upsert_vectors(vectors)
            results["success"].append(filename)
            logger.info(f"Uploaded and ingested: {filename} ({len(vectors)} vectors)")

        except Exception as e:
            results["errors"].append({"file": filename, "error": str(e)})
            logger.error(f"Upload error for {filename}: {e}")

    return results
