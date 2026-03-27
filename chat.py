"""
chat.py — RAG Chat com Gemini.

Pipeline:
1. Recebe pergunta do usuário
2. Gera embedding da pergunta (RETRIEVAL_QUERY)
3. Busca chunks relevantes no Pinecone
4. Monta contexto COM O TEXTO REAL dos chunks
5. Envia para o Gemini gerar resposta contextualizada
"""

from google import genai
from google.genai import types

from config import GEMINI_API_KEY
from embeddings import embed_query
from pinecone_db import search as pinecone_search

# Cliente Gemini para geração de texto
_client = genai.Client(api_key=GEMINI_API_KEY)

# Modelo de geração
GENERATION_MODEL = "gemini-2.5-flash"

# System prompt em português
SYSTEM_PROMPT = """Você é um assistente técnico especializado nos produtos da Hard CMP, uma empresa de fixadores, coberturas e componentes metálicos.

Você tem acesso a trechos extraídos de documentos internos da empresa (catálogos, desenhos técnicos, ebooks e folders). Os trechos são fornecidos como contexto junto com cada pergunta.

Regras:
- Responda SEMPRE em português brasileiro.
- Baseie suas respostas PRIMARIAMENTE no conteúdo dos trechos fornecidos.
- Seja preciso, técnico e detalhado quando a informação estiver disponível nos trechos.
- Cite o nome do documento e a página quando referenciar informações específicas (ex: "Conforme o Catálogo Hard CMP 2024, página 15...").
- Se a informação não estiver nos trechos fornecidos, diga claramente que não encontrou nos documentos disponíveis.
- Use formatação markdown: títulos, listas, negrito para termos técnicos.
- Organize a resposta de forma clara e estruturada.
"""


def build_context(results: list[dict]) -> str:
    """
    Monta texto de contexto RICO a partir dos resultados do Pinecone.
    Inclui o texto real dos chunks, não apenas o nome do arquivo.
    """
    if not results:
        return "Nenhum documento relevante encontrado no banco de dados."

    context_parts = []
    for i, result in enumerate(results, 1):
        meta = result.get("metadata", {})
        score = result.get("score", 0)
        filename = meta.get("filename", "Desconhecido")
        text = meta.get("text", "")
        type_label = meta.get("type_label", "")
        content_type = meta.get("content_type", "file_embedding")
        page_start = meta.get("page_start", "")
        page_end = meta.get("page_end", "")

        # Header do trecho
        page_info = ""
        if page_start:
            page_info = f" | Página(s): {page_start}"
            if page_end and page_end != page_start:
                page_info = f" | Páginas: {page_start}-{page_end}"

        header = f"[Trecho {i}] Fonte: {filename}{page_info} | Relevância: {score:.1%}"

        if content_type == "text_chunk" and text:
            context_parts.append(f"{header}\n{text}")
        elif text:
            context_parts.append(f"{header}\n{text}")
        else:
            context_parts.append(header)

    return "\n\n---\n\n".join(context_parts)


def chat(
    message: str,
    history: list[dict] | None = None,
    top_k: int = 8,
) -> dict:
    """
    Processa uma mensagem do usuário usando RAG.

    Args:
        message: Pergunta do usuário.
        history: Histórico de conversas.
        top_k: Quantidade de chunks para recuperar (aumentado para 8).

    Returns:
        Dict com resposta, documentos encontrados e metadados.
    """
    # 1. Busca chunks relevantes no Pinecone
    query_vector = embed_query(message)
    search_results = pinecone_search(
        query_vector=query_vector,
        top_k=top_k,
    )

    # 2. Monta contexto RICO com texto real
    context = build_context(search_results)

    # 3. Monta prompt com contexto RAG
    rag_prompt = f"""## Trechos Relevantes dos Documentos da Hard CMP:

{context}

---

## Pergunta do Usuário:
{message}

Responda a pergunta acima utilizando as informações dos trechos de documentos fornecidos. Cite a fonte (nome do documento e página) quando referenciar informações específicas."""

    # 4. Monta histórico
    contents = []
    if history:
        for msg in history[-10:]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=rag_prompt)],
        )
    )

    # 5. Gera resposta
    response = _client.models.generate_content(
        model=GENERATION_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.5,  # Reduzido para respostas mais precisas
            max_output_tokens=4096,  # Mais espaço para respostas detalhadas
        ),
    )

    answer = response.text if response.text else "Desculpe, não consegui gerar uma resposta."

    # 6. Prepara fontes (agrupa chunks do mesmo arquivo)
    sources_map = {}
    for r in search_results:
        meta = r.get("metadata", {})
        fname = meta.get("filename", "?")
        score = r.get("score", 0)
        page_start = meta.get("page_start", "")
        page_end = meta.get("page_end", "")

        if fname not in sources_map:
            sources_map[fname] = {
                "filename": fname,
                "score": score,
                "type_label": meta.get("type_label", ""),
                "file_type": meta.get("file_type", ""),
                "pages": [],
            }
        else:
            # Mantém o maior score
            sources_map[fname]["score"] = max(sources_map[fname]["score"], score)

        if page_start:
            if page_end and page_end != page_start:
                sources_map[fname]["pages"].extend(range(page_start, page_end + 1))
            else:
                sources_map[fname]["pages"].append(page_start)

    # Formata fontes
    sources = []
    for s in sources_map.values():
        pages = sorted(set(s["pages"]))
        page_str = ""
        if pages:
            page_str = f" (p. {', '.join(str(p) for p in pages[:10])})"
            if len(pages) > 10:
                page_str += "..."

        sources.append({
            "filename": s["filename"] + page_str,
            "score": round(s["score"], 4),
            "type_label": s["type_label"],
            "file_type": s["file_type"],
        })

    return {
        "answer": answer,
        "sources": sources,
        "model": GENERATION_MODEL,
        "chunks_used": len(search_results),
    }
