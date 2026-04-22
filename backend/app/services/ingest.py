"""
ingest.py — Pipeline de ingestão com chunking para PDFs.
"""

import os
import hashlib
import logging
from pathlib import Path
from datetime import datetime

from app.config import get_settings, SUPPORTED_EXTENSIONS
from app.services.embeddings import embed_file, embed_text, embed_texts_batch
from app.services.pinecone_db import init_index, upsert_vectors
from app.services.chunker import chunk_pdf, get_pdf_info

logger = logging.getLogger(__name__)


def generate_id(file_path: str, chunk_index: int | None = None) -> str:
    base = f"{file_path}::chunk::{chunk_index}" if chunk_index is not None else file_path
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def scan_directory(directory: str | None = None) -> list[dict]:
    """Escaneia diretorio em busca de arquivos suportados."""
    if directory is None:
        directory = get_settings().data_dir

    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    files = []
    for fp in dir_path.rglob("*"):
        if fp.is_file() and fp.suffix.lower() in SUPPORTED_EXTENSIONS:
            ext = fp.suffix.lower()
            stat = fp.stat()
            files.append({
                "path": str(fp.resolve()),
                "name": fp.name,
                "extension": ext,
                "mime_type": SUPPORTED_EXTENSIONS[ext],
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    return files


def ingest_pdf_chunked(filepath: str, filename: str, size_mb: float) -> list[dict]:
    """Ingere PDF com chunking."""
    pdf_info = get_pdf_info(filepath)

    if not pdf_info["has_text"]:
        logger.warning(f"{filename}: PDF sem texto, usando embedding de arquivo")
        embedding = embed_file(filepath, "application/pdf")
        return [{
            "id": generate_id(filepath),
            "values": embedding,
            "metadata": {
                "filename": filename, "filepath": filepath,
                "file_type": ".pdf", "mime_type": "application/pdf",
                "size_mb": size_mb, "type_label": "PDF",
                "content_type": "file_embedding",
                "text": f"[PDF sem texto: {filename}]",
                "allowed_personas": ["all"],
            },
        }]

    chunks = chunk_pdf(filepath)
    if not chunks:
        embedding = embed_file(filepath, "application/pdf")
        return [{
            "id": generate_id(filepath),
            "values": embedding,
            "metadata": {
                "filename": filename, "filepath": filepath,
                "file_type": ".pdf", "mime_type": "application/pdf",
                "size_mb": size_mb, "type_label": "PDF",
                "content_type": "file_embedding",
                "text": f"[PDF com pouco texto: {filename}]",
                "allowed_personas": ["all"],
            },
        }]

    logger.info(f"{filename}: {pdf_info['page_count']} pages -> {len(chunks)} chunks")

    # Batch embedding: coleta todos os textos e gera embeddings de uma vez
    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = embed_texts_batch(chunk_texts, task_type="RETRIEVAL_DOCUMENT")

    vectors = []
    for chunk, embedding in zip(chunks, embeddings):
        text_for_meta = chunk["text"][:8000]

        page_label = f"p.{chunk['page_start']}"
        if chunk["page_end"] != chunk["page_start"]:
            page_label = f"p.{chunk['page_start']}-{chunk['page_end']}"

        vectors.append({
            "id": generate_id(filepath, chunk["chunk_index"]),
            "values": embedding,
            "metadata": {
                "filename": filename, "filepath": filepath,
                "file_type": ".pdf", "mime_type": "application/pdf",
                "size_mb": size_mb, "type_label": f"PDF {page_label}",
                "content_type": "text_chunk",
                "chunk_index": chunk["chunk_index"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "word_count": chunk["word_count"],
                "text": text_for_meta,
                "allowed_personas": ["all"],
            },
        })

    return vectors


def ingest_file_whole(filepath: str, filename: str, ext: str, mime: str, size_mb: float) -> list[dict]:
    """Ingere arquivo nao-PDF como embedding inteiro."""
    embedding = embed_file(filepath, mime)
    return [{
        "id": generate_id(filepath),
        "values": embedding,
        "metadata": {
            "filename": filename, "filepath": filepath,
            "file_type": ext, "mime_type": mime,
            "size_mb": size_mb, "content_type": "file_embedding",
            "text": f"[{ext.upper().replace('.', '')} file: {filename}]",
            "allowed_personas": ["all"],
        },
    }]
