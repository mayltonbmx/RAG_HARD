"""
config.py — Settings via pydantic-settings.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    gemini_api_key: str
    pinecone_api_key: str

    # Pinecone
    pinecone_index_name: str = "rag-hard-multimodal"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    # Embedding
    embedding_model: str = "gemini-embedding-2-preview"
    embedding_dimensions: int = 768

    # Generation
    generation_model: str = "gemini-2.5-flash"

    # CORS
    allowed_origins: str = "http://localhost:3000"

    # Data directory
    data_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    # RAG settings
    min_score_threshold: float = 0.35

    # Admin login (genérico)
    admin_user: str = ""
    admin_password: str = ""
    jwt_secret: str = "change-me-in-production"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Supported file extensions
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
