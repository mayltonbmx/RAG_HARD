"""
chunker.py — Extração de texto de PDFs e fatiamento em chunks semânticos.

Estratégia de chunking semântico:
1. Extrai texto página a página
2. Detecta seções lógicas (títulos, quebras de duplo newline)
3. Agrupa parágrafos em chunks respeitando limites de tokens
4. Mantém sobreposição contextual entre chunks
5. Fallback para janela fixa quando seções não são detectáveis
"""

import re
import logging
import fitz  # PyMuPDF
from pathlib import Path

logger = logging.getLogger(__name__)

# Limites em PALAVRAS
MAX_CHUNK_WORDS = 600
MIN_CHUNK_WORDS = 80
OVERLAP_WORDS = 80


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


def _is_section_header(line: str) -> bool:
    """Detecta se uma linha é um título/cabeçalho de seção."""
    stripped = line.strip()
    if not stripped or len(stripped) < 3:
        return False

    # Linha inteira em UPPER CASE (ex: "ESPECIFICAÇÕES TÉCNICAS")
    if stripped.isupper() and len(stripped) > 4 and len(stripped.split()) <= 10:
        return True

    # Inicia com numeração de seção (ex: "1.", "2.3", "III.")
    if re.match(r'^[\d]+[\.\)]\s', stripped):
        return True
    if re.match(r'^[IVXLC]+[\.\)]\s', stripped):
        return True

    # Linha curta e em title case (ex: "Aplicações Recomendadas")
    words = stripped.split()
    if 2 <= len(words) <= 8 and stripped[0].isupper():
        # Se não termina com pontuação de frase, provavelmente é título
        if not stripped.endswith(('.', ',', ';', ':', '!')):
            upper_ratio = sum(1 for w in words if w[0].isupper()) / len(words)
            if upper_ratio >= 0.5:
                return True

    return False


def _split_into_paragraphs(text: str) -> list[str]:
    """Divide texto em parágrafos usando quebras duplas de linha."""
    # Normaliza quebras de linha
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Split em parágrafos (duplo newline ou mais)
    paragraphs = re.split(r'\n\s*\n', text)

    # Limpa e filtra parágrafos vazios
    result = []
    for p in paragraphs:
        cleaned = p.strip()
        if cleaned and len(cleaned) > 10:
            result.append(cleaned)

    return result


def _split_into_semantic_segments(pages: list[dict]) -> list[dict]:
    """Divide o texto em segmentos semânticos (seções ou parágrafos).

    Cada segmento tem: text, page_start, page_end
    """
    segments = []

    for page in pages:
        paragraphs = _split_into_paragraphs(page["text"])

        for para in paragraphs:
            lines = para.split('\n')
            current_segment = []

            for line in lines:
                if _is_section_header(line) and current_segment:
                    # Fecha segmento anterior antes do novo título
                    seg_text = '\n'.join(current_segment).strip()
                    if len(seg_text.split()) >= 10:
                        segments.append({
                            "text": seg_text,
                            "page_num": page["page_num"],
                        })
                    current_segment = [line]
                else:
                    current_segment.append(line)

            # Fecha último segmento da parágrafo
            if current_segment:
                seg_text = '\n'.join(current_segment).strip()
                if len(seg_text.split()) >= 10:
                    segments.append({
                        "text": seg_text,
                        "page_num": page["page_num"],
                    })

    return segments


def _merge_segments_into_chunks(segments: list[dict]) -> list[dict]:
    """Agrupa segmentos em chunks respeitando limites de tokens.

    Garante que nenhum parágrafo é cortado no meio.
    """
    if not segments:
        return []

    chunks = []
    current_texts = []
    current_words = 0
    current_page_start = segments[0]["page_num"]
    current_page_end = segments[0]["page_num"]

    for seg in segments:
        seg_words = len(seg["text"].split())

        # Se o segmento sozinho excede o máximo, faz split por palavras (fallback)
        if seg_words > MAX_CHUNK_WORDS:
            # Fecha chunk atual se houver
            if current_texts:
                chunks.append({
                    "text": "\n\n".join(current_texts),
                    "page_start": current_page_start,
                    "page_end": current_page_end,
                })
                current_texts = []
                current_words = 0

            # Fallback: divide segmento grande em janelas
            words = seg["text"].split()
            start = 0
            while start < len(words):
                end = min(start + MAX_CHUNK_WORDS, len(words))
                chunk_text = " ".join(words[start:end])
                if len(chunk_text.split()) >= MIN_CHUNK_WORDS:
                    chunks.append({
                        "text": chunk_text,
                        "page_start": seg["page_num"],
                        "page_end": seg["page_num"],
                    })
                start = end - OVERLAP_WORDS if end < len(words) else end
            continue

        # Se adicionar excederia o limite, fecha chunk atual
        if current_words + seg_words > MAX_CHUNK_WORDS and current_texts:
            chunks.append({
                "text": "\n\n".join(current_texts),
                "page_start": current_page_start,
                "page_end": current_page_end,
            })

            # Overlap: mantém último segmento para contexto
            last_text = current_texts[-1]
            last_words = len(last_text.split())
            if last_words <= OVERLAP_WORDS:
                current_texts = [last_text]
                current_words = last_words
            else:
                current_texts = []
                current_words = 0
            current_page_start = seg["page_num"]

        # Adiciona segmento ao chunk atual
        current_texts.append(seg["text"])
        current_words += seg_words
        current_page_end = seg["page_num"]

        if not current_texts or len(current_texts) == 1:
            current_page_start = seg["page_num"]

    # Fecha último chunk
    if current_texts and current_words >= MIN_CHUNK_WORDS:
        chunks.append({
            "text": "\n\n".join(current_texts),
            "page_start": current_page_start,
            "page_end": current_page_end,
        })

    return chunks


def chunk_pdf(pdf_path: str) -> list[dict]:
    """Extrai texto de um PDF e fatia em chunks semânticos com metadados."""
    filename = Path(pdf_path).name
    pages = extract_text_from_pdf(pdf_path)
    if not pages:
        return []

    # Passo 1: Dividir em segmentos semânticos
    segments = _split_into_semantic_segments(pages)

    if not segments:
        return []

    # Passo 2: Agrupar segmentos em chunks respeitando limites
    raw_chunks = _merge_segments_into_chunks(segments)

    # Passo 3: Formatar resultado
    result_chunks = []
    for i, chunk in enumerate(raw_chunks):
        result_chunks.append({
            "chunk_index": i,
            "text": chunk["text"],
            "page_start": chunk["page_start"],
            "page_end": chunk["page_end"],
            "word_count": len(chunk["text"].split()),
            "filename": filename,
        })

    logger.info(
        f"PDF '{filename}': {len(pages)} pages -> "
        f"{len(segments)} segments -> {len(result_chunks)} chunks "
        f"(avg {sum(c['word_count'] for c in result_chunks) // max(len(result_chunks), 1)} words/chunk)"
    )
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
