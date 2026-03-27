"""
chat_service.py — RAG Chat pipeline: busca contexto + gera resposta via Gemini.
"""

import logging
from google import genai
from google.genai import types

from app.config import get_settings
from app.services.embeddings import embed_query
from app.services.pinecone_db import search as pinecone_search

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

SYSTEM_PROMPT = """Voce e um assistente tecnico especializado nos produtos da Hard CMP, uma empresa de fixadores, coberturas e componentes metalicos.

Voce tem acesso a trechos extraidos de documentos internos da empresa (catalogos, desenhos tecnicos, ebooks e folders).

Regras:
- Responda SEMPRE em portugues brasileiro.
- Baseie suas respostas PRIMARIAMENTE no conteudo dos trechos fornecidos.
- Seja preciso, tecnico e detalhado quando a informacao estiver disponivel nos trechos.
- Cite o nome do documento e a pagina quando referenciar informacoes especificas.
- Se a informacao nao estiver nos trechos fornecidos, diga claramente.
- Use formatacao markdown: titulos, listas, negrito para termos tecnicos.
- Organize a resposta de forma clara e estruturada.
"""


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _build_context(results: list[dict]) -> str:
    """Monta contexto rico com texto real dos chunks."""
    if not results:
        return "Nenhum documento relevante encontrado."

    parts = []
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        score = r.get("score", 0)
        filename = meta.get("filename", "?")
        text = meta.get("text", "")
        page_start = meta.get("page_start", "")
        page_end = meta.get("page_end", "")

        page_info = ""
        if page_start:
            page_info = f" | Pagina(s): {page_start}"
            if page_end and page_end != page_start:
                page_info = f" | Paginas: {page_start}-{page_end}"

        header = f"[Trecho {i}] Fonte: {filename}{page_info} | Relevancia: {score:.1%}"
        parts.append(f"{header}\n{text}" if text else header)

    return "\n\n---\n\n".join(parts)


def chat(message: str, history: list[dict] | None = None, top_k: int = 8) -> dict:
    """Processa mensagem usando RAG."""
    settings = get_settings()
    client = _get_client()

    logger.info(f"Chat request: '{message[:80]}...' (top_k={top_k})")

    # 1. Busca chunks
    query_vector = embed_query(message)
    search_results = pinecone_search(query_vector=query_vector, top_k=top_k)
    logger.info(f"Found {len(search_results)} relevant chunks")

    # 2. Contexto rico
    context = _build_context(search_results)

    # 3. Prompt RAG
    rag_prompt = f"""## Trechos Relevantes dos Documentos da Hard CMP:

{context}

---

## Pergunta do Usuario:
{message}

Responda utilizando as informacoes dos trechos. Cite a fonte quando referenciar informacoes especificas."""

    # 4. Historico
    contents = []
    if history:
        for msg in history[-10:]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=rag_prompt)]))

    # 5. Gera resposta
    response = client.models.generate_content(
        model=settings.generation_model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.5,
            max_output_tokens=4096,
        ),
    )

    answer = response.text if response.text else "Desculpe, nao consegui gerar uma resposta."

    # 6. Fontes agrupadas
    sources_map: dict[str, dict] = {}
    for r in search_results:
        meta = r.get("metadata", {})
        fname = meta.get("filename", "?")
        score = r.get("score", 0)
        ps = meta.get("page_start", "")
        pe = meta.get("page_end", "")

        if fname not in sources_map:
            sources_map[fname] = {
                "filename": fname, "score": score,
                "type_label": meta.get("type_label", ""),
                "file_type": meta.get("file_type", ""),
                "pages": [],
            }
        else:
            sources_map[fname]["score"] = max(sources_map[fname]["score"], score)

        if ps:
            if pe and pe != ps:
                sources_map[fname]["pages"].extend(range(int(ps), int(pe) + 1))
            else:
                sources_map[fname]["pages"].append(int(ps))

    sources = []
    for s in sources_map.values():
        pages = sorted(set(s["pages"]))
        page_str = ""
        if pages:
            page_str = f" (p. {', '.join(str(p) for p in pages[:10])})"
        sources.append({
            "filename": s["filename"] + page_str,
            "score": round(s["score"], 4),
            "type_label": s["type_label"],
            "file_type": s["file_type"],
        })

    return {"answer": answer, "sources": sources, "model": settings.generation_model, "chunks_used": len(search_results)}
