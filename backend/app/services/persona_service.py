"""
persona_service.py — Gerenciamento de Personas (Especialistas Virtuais).

Persiste configurações no Pinecone (namespace "_personas").
Na primeira execução, injeta personas padrão para uso imediato.
"""

import json
import logging
import uuid
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

# Namespace dedicado para armazenar personas no Pinecone
_PERSONAS_NAMESPACE = "_personas"
_PERSONA_ID_PREFIX = "persona_"


def _get_index():
    """Retorna a referência ao índice Pinecone."""
    from app.services.pinecone_db import _get_index as get_pc_index
    return get_pc_index()


def _persona_to_vector(persona: dict) -> dict:
    """Converte uma persona dict em um vetor Pinecone para armazenamento.

    Usa vetor epsilon (não é para busca semântica, apenas armazenamento).
    As rules são salvas como JSON string no metadata porque o Pinecone
    tem limitações com listas de strings em metadados longos.
    """
    settings = get_settings()
    dim = settings.embedding_dimensions

    persona_id = f"{_PERSONA_ID_PREFIX}{persona['id']}"

    metadata = {
        "persona_id": persona["id"],
        "name": persona.get("name", ""),
        "description": persona.get("description", ""),
        "identity": persona.get("identity", ""),
        "rules_json": json.dumps(persona.get("rules", []), ensure_ascii=False),
        "temperature": persona.get("temperature", 0.5),
        "access_level": persona.get("access_level", "logged_in"),
        "is_default": persona.get("is_default", False),
        "content_type": "persona_config",
    }

    return {
        "id": persona_id,
        "values": [1e-7] * dim,
        "metadata": metadata,
    }


def _vector_to_persona(metadata: dict) -> dict:
    """Converte metadata Pinecone de volta para um dict de persona."""
    rules = []
    rules_raw = metadata.get("rules_json", "[]")
    try:
        rules = json.loads(rules_raw)
    except (json.JSONDecodeError, TypeError):
        rules = []

    return {
        "id": metadata.get("persona_id", ""),
        "name": metadata.get("name", ""),
        "description": metadata.get("description", ""),
        "identity": metadata.get("identity", ""),
        "rules": rules,
        "temperature": float(metadata.get("temperature", 0.5)),
        "access_level": metadata.get("access_level", "logged_in"),
        "is_default": bool(metadata.get("is_default", False)),
    }


def _read_all() -> list[dict]:
    """Lê todas as personas do Pinecone."""
    try:
        index = _get_index()
        settings = get_settings()
        dim = settings.embedding_dimensions

        results = index.query(
            vector=[0.0] * dim,
            top_k=100,
            include_metadata=True,
            namespace=_PERSONAS_NAMESPACE,
            filter={"content_type": {"$eq": "persona_config"}},
        )

        personas = []
        for match in results.matches:
            if match.metadata:
                persona = _vector_to_persona(match.metadata)
                if persona.get("id"):
                    personas.append(persona)

        logger.debug(f"Lidas {len(personas)} personas do Pinecone")
        return personas

    except Exception as e:
        logger.error(f"Erro ao ler personas do Pinecone: {e}")
        return []


def _write_one(persona: dict) -> None:
    """Grava uma persona no Pinecone."""
    try:
        index = _get_index()
        vector = _persona_to_vector(persona)
        index.upsert(vectors=[vector], namespace=_PERSONAS_NAMESPACE)
        logger.debug(f"Persona salva no Pinecone: {persona['name']}")
    except Exception as e:
        logger.error(f"Erro ao salvar persona no Pinecone: {e}")
        raise


def _delete_one(persona_id: str) -> None:
    """Remove uma persona do Pinecone."""
    try:
        index = _get_index()
        vector_id = f"{_PERSONA_ID_PREFIX}{persona_id}"
        index.delete(ids=[vector_id], namespace=_PERSONAS_NAMESPACE)
        logger.debug(f"Persona removida do Pinecone: {persona_id}")
    except Exception as e:
        logger.error(f"Erro ao remover persona do Pinecone: {e}")
        raise


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
    """Inicializa personas com os padrões, se o Pinecone estiver vazio."""
    personas = _read_all()
    if not personas:
        defaults = _get_default_personas()
        for persona in defaults:
            _write_one(persona)
        logger.info(f"Personas inicializadas no Pinecone com {len(defaults)} perfis padrão")
    else:
        logger.info(f"Personas carregadas do Pinecone: {len(personas)} perfis")


def list_personas(access_level: str | None = None) -> list[dict]:
    """Lista personas, opcionalmente filtrando por nível de acesso.

    - access_level=None: retorna todas (para painel administrativo).
    - access_level="public": retorna apenas públicas (Free).
    - access_level="logged_in": retorna públicas + assinantes.
    """
    personas = _read_all()

    if access_level is None:
        return personas

    allowed_levels = {"public"}
    if access_level == "logged_in":
        allowed_levels.add("logged_in")

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
            _write_one(p)

    _write_one(new_persona)
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
            if p["id"] != persona_id:
                p["is_default"] = False
                _write_one(p)

    # Aplica apenas campos enviados (não-None)
    clean_updates = {k: v for k, v in updates.items() if v is not None}
    target.update(clean_updates)

    _write_one(target)
    logger.info(f"Persona atualizada: {target['name']} (id={persona_id})")
    return target


def delete_persona(persona_id: str) -> bool:
    """Remove uma persona pelo ID."""
    personas = _read_all()
    exists = any(p["id"] == persona_id for p in personas)

    if not exists:
        return False

    _delete_one(persona_id)
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
