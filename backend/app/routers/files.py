"""
files.py — GET /api/files — Lista arquivos no diretorio data.
"""

from fastapi import APIRouter, HTTPException
from app.services.ingest import scan_directory

router = APIRouter(prefix="/api", tags=["files"])


@router.get("/files")
async def list_files():
    try:
        files = scan_directory()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
