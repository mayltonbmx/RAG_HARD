"""
personas.py — Rotas REST para gerenciamento de Especialistas Virtuais (Personas).

GET /api/personas          → Lista pública (filtra por nível de acesso)
POST /api/personas         → Cria nova persona (admin)
PUT /api/personas/{id}     → Edita persona (admin)
DELETE /api/personas/{id}  → Remove persona (admin)
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, status

from app.schemas.persona import (
    PersonaCreate, PersonaUpdate, PersonaResponse, PersonaListResponse,
)
from app.services.persona_service import (
    list_personas, get_persona, create_persona,
    update_persona, delete_persona,
)
from app.middleware.auth import require_admin_any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["personas"])


@router.get("/personas", response_model=PersonaListResponse)
async def list_personas_endpoint(access_level: str | None = None):
    """Lista personas disponíveis.

    - Sem filtro: retorna todas (para admin).
    - access_level=public: apenas públicas (visitante não logado).
    - access_level=logged_in: públicas + logadas.
    """
    personas = list_personas(access_level=access_level)
    return PersonaListResponse(personas=personas)


@router.get("/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona_endpoint(persona_id: str):
    """Retorna uma persona específica pelo ID."""
    persona = get_persona(persona_id)
    if persona is None:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_id}' não encontrada.")
    return persona


@router.post(
    "/personas",
    response_model=PersonaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_any)],
)
async def create_persona_endpoint(req: PersonaCreate):
    """Cria um novo especialista virtual. Requer autenticação de admin."""
    persona = create_persona(req.model_dump())
    logger.info(f"Persona criada via API: {persona['name']}")
    return persona


@router.put(
    "/personas/{persona_id}",
    response_model=PersonaResponse,
    dependencies=[Depends(require_admin_any)],
)
async def update_persona_endpoint(persona_id: str, req: PersonaUpdate):
    """Edita um especialista existente. Requer autenticação de admin."""
    updated = update_persona(persona_id, req.model_dump(exclude_unset=True))
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_id}' não encontrada.")
    logger.info(f"Persona atualizada via API: {updated['name']}")
    return updated


@router.delete(
    "/personas/{persona_id}",
    dependencies=[Depends(require_admin_any)],
)
async def delete_persona_endpoint(persona_id: str):
    """Remove um especialista. Requer autenticação de admin."""
    deleted = delete_persona(persona_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_id}' não encontrada.")
    logger.info(f"Persona removida via API: {persona_id}")
    return {"detail": f"Persona '{persona_id}' removida com sucesso."}
