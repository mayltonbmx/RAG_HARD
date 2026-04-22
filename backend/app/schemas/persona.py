"""
persona.py — Schemas Pydantic para o sistema de Multi-Personas (Especialistas Virtuais).
"""

from enum import Enum
from pydantic import BaseModel, Field


class AccessLevel(str, Enum):
    """Controla quem pode ver e usar a persona no chat."""
    public = "public"         # Qualquer visitante (não logado)
    logged_in = "logged_in"   # Apenas usuários autenticados
    admin = "admin"           # Apenas administradores


class PersonaBase(BaseModel):
    """Campos compartilhados entre criação e resposta."""
    name: str = Field(..., min_length=1, max_length=100, description="Nome do especialista")
    description: str = Field(default="", max_length=300, description="Descrição breve para o menu de seleção")
    identity: str = Field(default="", description="Texto que define quem o especialista é (identidade base)")
    rules: list[str] = Field(default_factory=list, max_length=15, description="Lista de até 15 regras de comportamento")
    temperature: float = Field(default=0.5, ge=0.0, le=1.0, description="Criatividade: 0.0=exato, 1.0=criativo")
    access_level: AccessLevel = Field(default=AccessLevel.logged_in, description="Nível de acesso necessário")
    is_default: bool = Field(default=False, description="Se é a persona padrão ao abrir o chat")


class PersonaCreate(PersonaBase):
    """Payload para criar um novo especialista."""
    pass


class PersonaUpdate(BaseModel):
    """Payload para edição parcial (todos os campos são opcionais)."""
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)
    identity: str | None = None
    rules: list[str] | None = Field(default=None, max_length=15)
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    access_level: AccessLevel | None = None
    is_default: bool | None = None


class PersonaResponse(PersonaBase):
    """Resposta completa de uma persona (inclui id)."""
    id: str


class PersonaListResponse(BaseModel):
    """Lista de personas para popular o dropdown do chat."""
    personas: list[PersonaResponse]
