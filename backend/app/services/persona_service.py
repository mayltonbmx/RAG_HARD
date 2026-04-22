"""
persona_service.py — Gerenciamento de Personas (Especialistas Virtuais).

Persiste configurações em data/personas.json.
Na primeira execução, injeta personas padrão para uso imediato.
"""

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

_PERSONAS_FILE: str | None = None


def _get_personas_path() -> Path:
    """Retorna o caminho do arquivo personas.json."""
    global _PERSONAS_FILE
    if _PERSONAS_FILE is None:
        settings = get_settings()
        _PERSONAS_FILE = os.path.join(settings.data_dir, "personas.json")
    return Path(_PERSONAS_FILE)


def _read_all() -> list[dict]:
    """Lê todas as personas do arquivo JSON."""
    path = _get_personas_path()
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Erro ao ler personas.json: {e}")
        return []


def _write_all(personas: list[dict]) -> None:
    """Grava todas as personas no arquivo JSON."""
    path = _get_personas_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(personas, f, ensure_ascii=False, indent=2)


def _get_default_personas() -> list[dict]:
    """Personas padrão injetadas na primeira execução."""
    return [
        {
            "id": "vendedor-tecnico",
            "name": "Vendedor Técnico",
            "description": "Especialista comercial nos produtos Hard, com foco em vendas consultivas.",
            "identity": (
                "Voce é um vendedor técnico, especializado nos produtos da Hard. "
                "A Hard Produtos para Construção é uma empresa com mais de 40 anos de história, "
                "que produz e comercializa fixadores, selantes e outras linhas de produtos, "
                "com foco na qualidade e longa duração. "
                "Devido a sua experiência você é um especialista admirado e tem o dom de ajudar "
                "a equipe a conhecer seus clientes para que eles atuem como um vendedor de vendas "
                "técnicas de alta performance."
            ),
            "rules": [
                "Responda SEMPRE em portugues brasileiro.",
                "Baseie suas respostas PRIMARIAMENTE no conteudo dos trechos fornecidos.",
                "Antes de ser preciso, faça perguntas inteligentes ao usuário sobre a aplicação do produto.",
                "Seja preciso, tecnico e detalhado conforme a interação do usuário vai fluindo.",
                "NUNCA inclua nomes de arquivos, documentos, paginas ou fontes nas suas respostas.",
                "Se a informacao nao estiver nos trechos fornecidos, diga claramente.",
                "Use formatacao markdown: titulos, listas, negrito para termos tecnicos.",
                "Organize a resposta de forma clara e estruturada.",
                "Mantenha um tom amigável e profissional, mas objetivo.",
                "Não entregue todo o conteúdo em uma unica resposta, ofereça caminhos.",
                "Sugira o melhor produto para a situação e dê insights de como a venda pode ser convertida."
            ],
            "temperature": 0.5,
            "access_level": "logged_in",
            "is_default": True,
        },
        {
            "id": "engenheiro",
            "name": "Engenheiro de Aplicação",
            "description": "Especialista técnico focado em especificações, normas e aplicações de engenharia.",
            "identity": (
                "Você é um engenheiro de aplicação sênior da Hard Produtos para Construção. "
                "Seu conhecimento abrange fixadores, selantes, normas ABNT, torques de aperto, "
                "resistência de materiais e especificações técnicas detalhadas. "
                "Você é metódico, preciso e adora resolver problemas complexos de aplicação."
            ),
            "rules": [
                "Responda SEMPRE em português brasileiro.",
                "Baseie suas respostas nos dados técnicos dos trechos fornecidos.",
                "Priorize especificações numéricas: dimensões, torques, resistências, normas.",
                "Quando relevante, mencione normas técnicas aplicáveis (ABNT, ISO, DIN).",
                "Se a informação técnica não estiver nos trechos, diga claramente.",
                "Use formatação markdown com tabelas quando comparar especificações.",
                "NUNCA inclua nomes de arquivos ou fontes nas respostas.",
                "Seja direto e técnico, sem rodeios comerciais."
            ],
            "temperature": 0.2,
            "access_level": "logged_in",
            "is_default": False,
        },
        {
            "id": "treinadora",
            "name": "Treinadora Comercial",
            "description": "Mentora de vendas que capacita a equipe com técnicas e conhecimento de produto.",
            "identity": (
                "Você é uma treinadora comercial experiente da Hard Produtos para Construção. "
                "Seu papel é capacitar vendedores e representantes, ensinando técnicas de abordagem, "
                "argumentação de vendas e conhecimento profundo de produto. "
                "Você é encorajadora, didática e sempre conecta o conhecimento técnico com "
                "situações reais de vendas no balcão ou em campo."
            ),
            "rules": [
                "Responda SEMPRE em português brasileiro.",
                "Use os trechos para ensinar sobre produtos de forma didática.",
                "Dê exemplos práticos de como usar o conhecimento na venda.",
                "Simule objeções de clientes e ensine como rebatê-las.",
                "Seja encorajadora e motivacional, mas com base em dados reais.",
                "Use formatação markdown para organizar dicas e passos.",
                "NUNCA inclua nomes de arquivos ou fontes nas respostas.",
                "Conecte sempre o produto à necessidade real do cliente final."
            ],
            "temperature": 0.6,
            "access_level": "logged_in",
            "is_default": False,
        },
    ]


# ========================= CRUD =========================

def init_personas() -> None:
    """Inicializa o arquivo de personas com os padrões, se não existir."""
    path = _get_personas_path()
    if not path.exists():
        defaults = _get_default_personas()
        _write_all(defaults)
        logger.info(f"Personas inicializadas com {len(defaults)} perfis padrão")
    else:
        personas = _read_all()
        logger.info(f"Personas carregadas: {len(personas)} perfis")


def list_personas(access_level: str | None = None) -> list[dict]:
    """Lista personas, opcionalmente filtrando por nível de acesso.

    - access_level=None: retorna todas (para admin).
    - access_level="public": retorna apenas públicas.
    - access_level="logged_in": retorna públicas + logged_in.
    """
    personas = _read_all()

    if access_level is None:
        return personas

    allowed_levels = {"public"}
    if access_level in ("logged_in", "admin"):
        allowed_levels.add("logged_in")
    if access_level == "admin":
        allowed_levels.add("admin")

    return [p for p in personas if p.get("access_level", "logged_in") in allowed_levels]


def get_persona(persona_id: str) -> Optional[dict]:
    """Busca persona por ID."""
    personas = _read_all()
    for p in personas:
        if p["id"] == persona_id:
            return p
    return None


def get_default_persona() -> Optional[dict]:
    """Retorna a persona marcada como padrão."""
    personas = _read_all()
    for p in personas:
        if p.get("is_default", False):
            return p
    return personas[0] if personas else None


def create_persona(data: dict) -> dict:
    """Cria uma nova persona."""
    personas = _read_all()

    # Gera ID a partir do nome (slug) ou UUID
    persona_id = data.get("id") or _slugify(data["name"])

    # Garante ID único
    existing_ids = {p["id"] for p in personas}
    if persona_id in existing_ids:
        persona_id = f"{persona_id}-{uuid.uuid4().hex[:6]}"

    new_persona = {**data, "id": persona_id}

    # Se marcou como default, desmarca as outras
    if new_persona.get("is_default", False):
        for p in personas:
            p["is_default"] = False

    personas.append(new_persona)
    _write_all(personas)
    logger.info(f"Persona criada: {new_persona['name']} (id={persona_id})")
    return new_persona


def update_persona(persona_id: str, updates: dict) -> Optional[dict]:
    """Atualiza campos de uma persona existente."""
    personas = _read_all()

    target = None
    for p in personas:
        if p["id"] == persona_id:
            target = p
            break

    if target is None:
        return None

    # Se está marcando como default, desmarca as outras
    if updates.get("is_default", False):
        for p in personas:
            p["is_default"] = False

    # Aplica apenas campos enviados (não-None)
    clean_updates = {k: v for k, v in updates.items() if v is not None}
    target.update(clean_updates)

    _write_all(personas)
    logger.info(f"Persona atualizada: {target['name']} (id={persona_id})")
    return target


def delete_persona(persona_id: str) -> bool:
    """Remove uma persona pelo ID."""
    personas = _read_all()
    original_count = len(personas)
    personas = [p for p in personas if p["id"] != persona_id]

    if len(personas) == original_count:
        return False

    _write_all(personas)
    logger.info(f"Persona removida: {persona_id}")
    return True


# ========================= UTILS =========================

def build_system_prompt(persona: dict) -> str:
    """Monta o system prompt completo a partir de identity + rules da persona.

    Formato final:
    <identity>

    Voce tem acesso a trechos extraidos de documentos internos da empresa.

    Regras:
    - Regra 1
    - Regra 2
    ...
    """
    identity = persona.get("identity", "").strip()
    rules = persona.get("rules", [])

    parts = []

    if identity:
        parts.append(identity)

    # Contexto fixo (sempre presente, independente da persona)
    parts.append(
        "Voce tem acesso a trechos extraidos de documentos internos da empresa "
        "(catalogos, desenhos tecnicos, ebooks e folders)."
    )

    if rules:
        rules_text = "\n".join(f"- {rule}" for rule in rules if rule.strip())
        parts.append(f"Regras:\n{rules_text}")

    return "\n\n".join(parts)


def _slugify(text: str) -> str:
    """Converte texto em slug simples para ID."""
    import re
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:50]
