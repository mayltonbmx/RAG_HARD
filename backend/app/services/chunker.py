"""
chunker.py — Extração de texto de PDFs e fatiamento em chunks.
"""

import logging
import fitz  # PyMuPDF
from pathlib import Path

logger = logging.getLogger(__name__)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
MIN_CHUNK_SIZE = 50


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """Extrai texto página a página."""
    doc = fitz.open(pdf_path)
    pages = []
    for i in range(len(doc)):
        text = doc[i].get_text("text").strip()
        if text:
            pages.append({"page_num": i + 1, "text": text, "char_count": len(text)})
    doc.close()
    return pages


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Fatia texto em chunks com sobreposição."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text] if len(words) >= MIN_CHUNK_SIZE else []

    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        if len(chunk_words) >= MIN_CHUNK_SIZE:
            chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
        start += step

    return chunks


def chunk_pdf(pdf_path: str) -> list[dict]:
    """Extrai texto de um PDF e fatia em chunks com metadados."""
    filename = Path(pdf_path).name
    pages = extract_text_from_pdf(pdf_path)
    if not pages:
        return []

    full_text_parts = []
    page_boundaries = []
    current_pos = 0

    for page in pages:
        separator = f"\n\n--- [Pagina {page['page_num']}] ---\n\n"
        full_text_parts.append(separator)
        full_text_parts.append(page["text"])
        text_with_sep = separator + page["text"]
        page_boundaries.append({
            "start": current_pos,
            "end": current_pos + len(text_with_sep),
            "page_num": page["page_num"],
        })
        current_pos += len(text_with_sep)

    full_text = "".join(full_text_parts)
    raw_chunks = chunk_text(full_text)

    result_chunks = []
    search_pos = 0

    for i, chunk_content in enumerate(raw_chunks):
        chunk_start = full_text.find(chunk_content[:100], search_pos)
        if chunk_start == -1:
            chunk_start = search_pos
        chunk_end = chunk_start + len(chunk_content)
        search_pos = max(chunk_start + 1, search_pos)

        page_start = page_end = None
        for boundary in page_boundaries:
            if boundary["start"] <= chunk_start < boundary["end"]:
                if page_start is None:
                    page_start = boundary["page_num"]
            if boundary["start"] < chunk_end <= boundary["end"]:
                page_end = boundary["page_num"]

        result_chunks.append({
            "chunk_index": i,
            "text": chunk_content,
            "page_start": page_start or 1,
            "page_end": page_end or (page_start or 1),
            "word_count": len(chunk_content.split()),
            "filename": filename,
        })

    logger.info(f"PDF '{filename}': {len(pages)} pages -> {len(result_chunks)} chunks")
    return result_chunks


def get_pdf_info(pdf_path: str) -> dict:
    """Info basica sobre o PDF."""
    doc = fitz.open(pdf_path)
    info = {"page_count": len(doc), "has_text": False, "text_pages": 0}
    for i in range(len(doc)):
        if doc[i].get_text("text").strip():
            info["has_text"] = True
            info["text_pages"] += 1
    doc.close()
    return info
