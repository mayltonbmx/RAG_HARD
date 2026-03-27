"""
config.py — Carregamento de variáveis de ambiente e constantes de configuração.
"""

import os
import sys
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()


def _require_env(name: str) -> str:
    """Retorna o valor de uma variável de ambiente ou encerra com erro."""
    value = os.getenv(name)
    if not value or value.startswith("your-"):
        print(f"❌ Variável de ambiente '{name}' não configurada.")
        print(f"   Edite o arquivo .env e insira o valor correto.")
        sys.exit(1)
    return value


# --- Chaves de API ---
GEMINI_API_KEY: str = _require_env("GEMINI_API_KEY")
PINECONE_API_KEY: str = _require_env("PINECONE_API_KEY")

# --- Pinecone ---
PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "rag-hard-multimodal")
PINECONE_CLOUD: str = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION: str = os.getenv("PINECONE_REGION", "us-east-1")

# --- Embedding ---
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2-preview")
EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))

# --- Tipos de arquivo suportados ---
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".mp4": "video/mp4",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".webp": "image/webp",
}

# --- Limites ---
MAX_VIDEO_DURATION_SECONDS: int = 120
MAX_INPUT_TOKENS: int = 8192
