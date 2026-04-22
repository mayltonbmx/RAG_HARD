"""
models.py — Pydantic request/response schemas.
"""

from pydantic import BaseModel, Field


# =================== CHAT ===================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensagem do usuario")
    history: list[dict] | None = Field(default=None, description="Historico da conversa")
    top_k: int = Field(default=8, ge=1, le=20, description="Chunks para recuperar")
    persona_id: str | None = Field(default=None, description="ID do especialista virtual selecionado")


class SourceItem(BaseModel):
    filename: str
    score: float
    type_label: str = ""
    file_type: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    model: str
    chunks_used: int


# =================== SEARCH ===================

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    file_type: str | None = None


class SearchResult(BaseModel):
    id: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str


# =================== STATS ===================

class StatsResponse(BaseModel):
    total_vectors: int
    dimension: int
    index_fullness: float
    model: str
    total_files: int


# =================== HEALTH ===================

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "2.0.0"
    services: dict[str, str] = {}


# =================== FILES ===================

class FileItem(BaseModel):
    path: str
    name: str
    extension: str
    mime_type: str
    size_mb: float
    modified: str


class FilesResponse(BaseModel):
    files: list[FileItem]


# =================== UPLOAD ===================

class UploadResponse(BaseModel):
    success: list[str] = []
    errors: list[dict] = []
