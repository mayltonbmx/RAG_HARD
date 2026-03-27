"""
embeddings.py — Geração de embeddings multimodais via Gemini Embedding 2.

Suporta: texto, imagem (PNG/JPEG/WebP), vídeo (MP4), áudio (MP3/WAV) e PDF.
"""

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS

# Cliente do Gemini (inicializado uma vez)
_client = genai.Client(api_key=GEMINI_API_KEY)


def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    """
    Gera embedding de texto puro.

    Args:
        text: Texto para gerar embedding.
        task_type: Tipo de tarefa (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.).

    Returns:
        Lista de floats representando o vetor de embedding.
    """
    result = _client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )
    return result.embeddings[0].values


def embed_file(file_path: str, mime_type: str) -> list[float]:
    """
    Gera embedding de um arquivo (imagem, vídeo, áudio ou PDF).

    Args:
        file_path: Caminho absoluto para o arquivo.
        mime_type: MIME type do arquivo (ex: 'application/pdf', 'image/png').

    Returns:
        Lista de floats representando o vetor de embedding.
    """
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    result = _client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=types.Content(
            parts=[
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type,
                ),
            ]
        ),
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )
    return result.embeddings[0].values


def embed_image(file_path: str) -> list[float]:
    """Gera embedding de uma imagem (PNG, JPEG, WebP)."""
    import mimetypes
    mime, _ = mimetypes.guess_type(file_path)
    return embed_file(file_path, mime or "image/png")


def embed_video(file_path: str) -> list[float]:
    """Gera embedding de um vídeo MP4 (≤ 120 segundos)."""
    return embed_file(file_path, "video/mp4")


def embed_audio(file_path: str) -> list[float]:
    """Gera embedding de áudio (MP3, WAV)."""
    import mimetypes
    mime, _ = mimetypes.guess_type(file_path)
    return embed_file(file_path, mime or "audio/mpeg")


def embed_pdf(file_path: str) -> list[float]:
    """Gera embedding de um documento PDF."""
    return embed_file(file_path, "application/pdf")


def embed_query(text: str) -> list[float]:
    """
    Gera embedding otimizado para consultas de busca.
    Usa task_type=RETRIEVAL_QUERY para melhor performance na busca.
    """
    return embed_text(text, task_type="RETRIEVAL_QUERY")
