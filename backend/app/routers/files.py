"""
files.py — GET /api/files — Lista arquivos no diretorio data (requires Admin role).
"""

from fastapi import APIRouter, HTTPException, Depends
from app.services.ingest import scan_directory
from app.middleware.auth import azure_scheme, require_admin

router = APIRouter(prefix="/api", tags=["files"])

_deps = [Depends(azure_scheme), Depends(require_admin)] if azure_scheme else [Depends(require_admin)]


@router.get("/files", dependencies=_deps)
async def list_files():
    try:
        files = scan_directory()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
