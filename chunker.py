"""
chunker.py — Extração de texto de PDFs e fatiamento em chunks com sobreposição.

Estratégia:
- Extrai texto de cada página do PDF via PyMuPDF
- Fatia o texto em chunks de ~800 palavras com ~150 palavras de sobreposição
- Preserva metadados: número da página, posição no documento
- Para arquivos não-PDF (imagens, vídeos), mantém o embedding por arquivo inteiro
"""

import fitz  # PyMuPDF
from pathlib import Path

# Configuração de chunking
CHUNK_SIZE = 800       # palavras por chunk
CHUNK_OVERLAP = 150    # palavras de sobreposição entre chunks
MIN_CHUNK_SIZE = 50    # mínimo de palavras para criar um chunk


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extrai texto página a página de um PDF.

    Args:
        pdf_path: Caminho absoluto para o PDF.

    Returns:
        Lista de dicts com:
            - page_num (int): número da página (1-indexed)
            - text (str): texto extraído da página
            - char_count (int): total de caracteres na página
    """
    doc = fitz.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()

        if text:  # Ignora páginas sem texto (capas com imagem, etc.)
            pages.append({
                "page_num": page_num + 1,
                "text": text,
                "char_count": len(text),
            })

    doc.close()
    return pages


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """
    Fatia texto em chunks com sobreposição.

    Args:
        text: Texto para fatiar.
        chunk_size: Número de palavras por chunk.
        overlap: Número de palavras de sobreposição.

    Returns:
        Lista de strings, cada uma sendo um chunk do texto.
    """
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
    """
    Extrai texto de um PDF e fatia em chunks com metadados.

    Args:
        pdf_path: Caminho absoluto para o PDF.

    Returns:
        Lista de dicts com:
            - chunk_index (int): índice do chunk
            - text (str): texto do chunk
            - page_start (int): página inicial do chunk
            - page_end (int): página final do chunk
            - word_count (int): contagem de palavras
            - filename (str): nome do arquivo
    """
    filename = Path(pdf_path).name
    pages = extract_text_from_pdf(pdf_path)

    if not pages:
        return []

    # Concatena todas as páginas com marcadores de página
    full_text_parts = []
    page_boundaries = []  # (char_start, char_end, page_num)

    current_pos = 0
    for page in pages:
        separator = f"\n\n--- [Página {page['page_num']}] ---\n\n"
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

    # Fatia o texto completo em chunks
    raw_chunks = chunk_text(full_text)

    # Monta chunks com metadados de página
    result_chunks = []
    search_pos = 0

    for i, chunk_text_content in enumerate(raw_chunks):
        # Encontra em qual posição do texto completo este chunk está
        chunk_start = full_text.find(chunk_text_content[:100], search_pos)
        if chunk_start == -1:
            chunk_start = search_pos
        chunk_end = chunk_start + len(chunk_text_content)
        search_pos = max(chunk_start + 1, search_pos)

        # Determina páginas abrangidas
        page_start = None
        page_end = None
        for boundary in page_boundaries:
            if boundary["start"] <= chunk_start < boundary["end"]:
                if page_start is None:
                    page_start = boundary["page_num"]
            if boundary["start"] < chunk_end <= boundary["end"]:
                page_end = boundary["page_num"]

        if page_start is None:
            page_start = 1
        if page_end is None:
            page_end = page_start

        result_chunks.append({
            "chunk_index": i,
            "text": chunk_text_content,
            "page_start": page_start,
            "page_end": page_end,
            "word_count": len(chunk_text_content.split()),
            "filename": filename,
        })

    return result_chunks


def get_pdf_info(pdf_path: str) -> dict:
    """Retorna informações básicas sobre o PDF."""
    doc = fitz.open(pdf_path)
    info = {
        "page_count": len(doc),
        "has_text": False,
        "text_pages": 0,
    }

    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text").strip()
        if text:
            info["has_text"] = True
            info["text_pages"] += 1

    doc.close()
    return info
