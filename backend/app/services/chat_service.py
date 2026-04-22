"""
chat_service.py — RAG Chat pipeline: busca contexto + gera resposta via Gemini.
"""

import json
import logging
import time
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

from app.config import get_settings
from app.services.embeddings import embed_query
from app.services.pinecone_db import search as pinecone_search
from app.services.persona_service import get_persona, get_default_persona, build_system_prompt
from app.services.analytics import log_chat_event

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

# Fallback usado APENAS se o sistema de personas não estiver disponível.
# Em operação normal, o prompt é montado dinamicamente via persona_service.
_FALLBACK_SYSTEM_PROMPT = """Voce é um vendedor técnico, especializado nos produtos da Hard. A Hard Produtos para Construção é uma empresa com mais de 40 anos de história, que produz e comercializa fixadores, selantes e outras linhas de produtos, com foco na qualidade e longa duração.
Devido a sua experiência você é um especialista admirado e tem o dom de ajudar a equipe a conhecer seus clientes para que eles atuem como um vendedor de vendas técnicas de alta performance.

Voce tem acesso a trechos extraidos de documentos internos da empresa (catalogos, desenhos tecnicos, ebooks e folders).

Regras:
- Responda SEMPRE em portugues brasileiro.
- Baseie suas respostas PRIMARIAMENTE no conteudo dos trechos fornecidos.
- Antes de ser preciso, técnico e detalhado, busque parametrizar o cliente ou a aplicação do produto, fazendo perguntas inteligentes ao usuário, por exemplo para qual aplicação será o produto...
- Seja preciso, tecnico e seja detalhado conforme a interação do usuário vai fluindo.
- NUNCA inclua nomes de arquivos, documentos, paginas ou fontes nas suas respostas. O usuario nao precisa saber de onde veio a informacao. Apenas use o conteudo dos trechos para responder.
- Se a informacao nao estiver nos trechos fornecidos, diga claramente.
- Use formatacao markdown: titulos, listas, negrito para termos tecnicos.
- Organize a resposta de forma clara e estruturada.
- Certifique-se de que as respostas sejam precisas e úteis.
- Mantenha um tom amigável e profissional. Mas seja objetivo, conforme a conversa evolui voce vai detalhando cada vez mais, acompanhando a compreensão do usuário do chat.
-Não entregue toda o conteúdo em uma unica resposta, ofereça caminhos para o usuário, sobre aplicações, sobre especificações, algo conectado ao assunto.
-Não esqueça que você também é um vendedor, então sugira o melhor produto para a situação e de insights de como a venda pode ser convertida com sucesso.
"""


def _resolve_persona(persona_id: str | None) -> tuple[str, float]:
    """Resolve persona_id em (system_prompt, temperature).

    Fallback seguro: se persona não existir, usa o prompt original.
    Isso garante que o deploy atual não quebre.
    """
    if persona_id:
        persona = get_persona(persona_id)
        if persona:
            prompt = build_system_prompt(persona)
            temp = persona.get("temperature", 0.5)
            logger.info(f"Persona ativa: {persona['name']} (id={persona_id}, temp={temp})")
            return prompt, temp
        logger.warning(f"Persona '{persona_id}' não encontrada, usando fallback")

    # Tenta persona padrão
    default = get_default_persona()
    if default:
        prompt = build_system_prompt(default)
        temp = default.get("temperature", 0.5)
        logger.info(f"Persona padrão: {default['name']} (temp={temp})")
        return prompt, temp

    # Último recurso: prompt original hardcoded
    return _FALLBACK_SYSTEM_PROMPT, 0.5


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

        header = f"[Trecho {i}]"
        parts.append(f"{header}\n{text}" if text else header)

    return "\n\n---\n\n".join(parts)


def _rewrite_query(client, model: str, message: str, history: list[dict]) -> str:
    """Reescreve a query incorporando contexto do histórico da conversa.

    Isso resolve o problema de follow-up: 'E o preço?' → 'Qual é o preço do parafuso X da Hard?'
    """
    # Monta resumo compacto das últimas mensagens
    recent = history[-4:]  # Últimas 4 mensagens para contexto
    history_text = "\n".join(
        f"{'Usuário' if m['role'] == 'user' else 'Assistente'}: {m['content'][:200]}"
        for m in recent
    )

    rewrite_prompt = f"""Dado o histórico abaixo e a nova pergunta do usuário, reescreva a pergunta de forma autônoma e completa, incorporando o contexto necessário para uma busca semântica eficaz.

Histórico recente:
{history_text}

Nova pergunta: {message}

Responda APENAS com a pergunta reescrita, sem explicações. Se a pergunta já é autônoma, repita-a."""

    try:
        response = client.models.generate_content(
            model=model,
            contents=rewrite_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=200,
            ),
        )
        rewritten = response.text.strip() if response.text else message
        if rewritten and len(rewritten) > 5:
            logger.info(f"Query rewritten: '{message[:60]}' -> '{rewritten[:60]}'")
            return rewritten
    except Exception as e:
        logger.warning(f"Query rewrite failed, using original: {e}")

    return message


def _classify_intent(client, model: str, query: str) -> dict:
    """Classifica a intent da query para ajustar parâmetros de busca.

    Intents possíveis:
    - 'tecnica': especificação técnica detalhada → top_k alto
    - 'comparacao': comparação entre produtos → top_k alto + busca ampla
    - 'aplicacao': recomendação de produto para aplicação → top_k médio
    - 'geral': pergunta geral → top_k padrão
    """
    classify_prompt = f"""Classifique a intenção da pergunta abaixo em UMA das categorias:
- tecnica: pergunta sobre especificações técnicas, dimensões, materiais, normas
- comparacao: comparação entre produtos ou linhas de produtos
- aplicacao: qual produto usar para uma aplicação específica
- geral: saudação, pergunta genérica ou outro

Pergunta: {query}

Responda APENAS com a categoria (uma palavra)."""

    intent_config = {
        "tecnica": {"top_k_boost": 4, "filter": None},
        "comparacao": {"top_k_boost": 6, "filter": None},
        "aplicacao": {"top_k_boost": 2, "filter": None},
        "geral": {"top_k_boost": 0, "filter": None},
    }

    try:
        response = client.models.generate_content(
            model=model,
            contents=classify_prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=20,
            ),
        )
        if response.text:
            intent = response.text.strip().lower().replace(".", "")
            if intent in intent_config:
                logger.info(f"Intent classified: '{intent}' for query: '{query[:50]}'")
                return {"intent": intent, **intent_config[intent]}
    except Exception as e:
        logger.warning(f"Intent classification failed: {e}")

    return {"intent": "geral", **intent_config["geral"]}


def _rerank_results(client, model: str, query: str, results: list[dict], top_n: int = 5) -> list[dict]:
    """Re-ranker leve usando Gemini para reordenar chunks por relevância semântica.

    O cosine similarity do Pinecone é bom, mas um re-ranker cross-encoder
    captura nuances que a busca vetorial pode perder.
    """
    if len(results) <= 2:
        return results  # Não vale re-rankar poucos resultados

    # Monta prompt compacto para scoring
    chunks_text = ""
    for i, r in enumerate(results):
        text = r.get("metadata", {}).get("text", "")[:300]
        chunks_text += f"\n[{i}] {text}\n"

    rerank_prompt = f"""Avalie a relevância de cada trecho abaixo para a consulta do usuário.
Para cada trecho, atribua uma nota de 0 a 10 (10 = extremamente relevante).

Consulta: {query}

Trechos:
{chunks_text}

Responda APENAS no formato: 0:nota,1:nota,2:nota,...
Exemplo: 0:8,1:3,2:9"""

    try:
        response = client.models.generate_content(
            model=model,
            contents=rerank_prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=100,
            ),
        )

        if response.text:
            # Parse scores: "0:8,1:3,2:9" -> {0: 8, 1: 3, 2: 9}
            scores = {}
            for pair in response.text.strip().split(","):
                pair = pair.strip()
                if ":" in pair:
                    idx_str, score_str = pair.split(":", 1)
                    try:
                        scores[int(idx_str.strip())] = float(score_str.strip())
                    except ValueError:
                        continue

            if scores:
                # Re-ordena por score do re-ranker
                scored_results = []
                for i, r in enumerate(results):
                    rerank_score = scores.get(i, 5.0)  # Default 5 se não encontrado
                    r["rerank_score"] = rerank_score
                    scored_results.append(r)

                scored_results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
                logger.info(f"Re-ranked {len(scored_results)} results, top score: {scored_results[0].get('rerank_score', '?')}")
                return scored_results[:top_n]

    except Exception as e:
        logger.warning(f"Re-ranking failed, using original order: {e}")

    return results[:top_n]


def _prepare_chat_context(message: str, history: list[dict] | None, top_k: int, persona_id: str | None = None) -> dict:
    """Prepara o contexto RAG: query rewriting, busca, re-ranking, histórico.

    Retorna dict com: contents, search_results, settings, rag_prompt
    """
    settings = get_settings()
    client = _get_client()

    logger.info(f"Chat request: '{message[:80]}...' (top_k={top_k})")

    # 1. Query rewriting (se houver histórico)
    search_query = message
    if history and len(history) >= 2:
        search_query = _rewrite_query(client, settings.generation_model, message, history)

    # 2. Classificação de intent
    intent_info = _classify_intent(client, settings.generation_model, search_query)
    effective_top_k = top_k + intent_info["top_k_boost"]

    # 3. Busca chunks com query reescrita (busca mais para re-ranking)
    query_vector = embed_query(search_query)

    # Filtro de conhecimento por persona: só retorna chunks acessíveis
    search_filter = None
    if persona_id:
        search_filter = {
            "$or": [
                {"allowed_personas": {"$exists": False}},   # arquivos sem restrição (legado)
                {"allowed_personas": {"$size": 0}},         # lista vazia = todos
                {"allowed_personas": {"$in": [persona_id]}}, # persona tem acesso
            ]
        }

    search_results = pinecone_search(
        query_vector=query_vector,
        top_k=effective_top_k + 4,
        min_score=settings.min_score_threshold,
        filter_dict=search_filter,
    )
    logger.info(f"Found {len(search_results)} chunks (intent={intent_info['intent']}, effective_top_k={effective_top_k}, persona_filter={'yes' if persona_id else 'no'})")

    # 4. Re-ranking dos resultados
    search_results = _rerank_results(client, settings.generation_model, search_query, search_results, top_n=effective_top_k)

    # 5. Contexto rico
    context = _build_context(search_results)

    # 6. Prompt RAG
    rag_prompt = f"""## Trechos Relevantes dos Documentos da Hard:

{context}

---

## Pergunta do Usuario:
{message}

Responda utilizando as informacoes dos trechos. Nao cite fontes ou referencias a menos que o usuario solicite explicitamente."""

    # 7. Historico (limitado por tokens estimados)
    MAX_HISTORY_TOKENS = 4000
    contents = []
    if history:
        trimmed = []
        token_count = 0
        for msg in reversed(history):
            msg_tokens = len(msg["content"]) // 4
            if token_count + msg_tokens > MAX_HISTORY_TOKENS:
                break
            trimmed.append(msg)
            token_count += msg_tokens

        trimmed.reverse()
        logger.info(f"History: {len(trimmed)}/{len(history)} messages (~{token_count} tokens)")

        for msg in trimmed:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=rag_prompt)]))

    # Resolve persona dinâmica
    system_prompt, temperature = _resolve_persona(persona_id)

    return {
        "contents": contents,
        "search_results": search_results,
        "settings": settings,
        "client": client,
        "search_query": search_query,
        "intent": intent_info["intent"],
        "start_time": time.perf_counter(),
        "system_prompt": system_prompt,
        "temperature": temperature,
    }


def _build_sources(search_results: list[dict]) -> list[dict]:
    """Agrupa e formata fontes dos chunks utilizados."""
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
    return sources


def chat(message: str, history: list[dict] | None = None, top_k: int = 8, persona_id: str | None = None) -> dict:
    """Processa mensagem usando RAG (resposta completa, sem streaming)."""
    ctx = _prepare_chat_context(message, history, top_k, persona_id=persona_id)

    # 8. Gera resposta (com retry para erros transientes)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8),
           before_sleep=before_sleep_log(logger, logging.WARNING), reraise=True)
    def _generate():
        return ctx["client"].models.generate_content(
            model=ctx["settings"].generation_model,
            contents=ctx["contents"],
            config=types.GenerateContentConfig(
                system_instruction=ctx["system_prompt"],
                temperature=ctx["temperature"],
                max_output_tokens=4096,
            ),
        )

    response = _generate()

    answer = response.text if response.text else "Desculpe, nao consegui gerar uma resposta."

    # 9. Fontes
    sources = _build_sources(ctx["search_results"])

    # 10. Analytics
    latency_ms = (time.perf_counter() - ctx["start_time"]) * 1000
    scores = [r.get("score", 0) for r in ctx["search_results"]]
    avg_score = sum(scores) / len(scores) if scores else 0
    try:
        log_chat_event(
            query=message,
            rewritten_query=ctx.get("search_query"),
            intent=ctx.get("intent", "geral"),
            latency_ms=latency_ms,
            chunks_used=len(ctx["search_results"]),
            avg_score=avg_score,
            model=ctx["settings"].generation_model,
        )
    except Exception as e:
        logger.warning(f"Analytics log failed: {e}")

    return {"answer": answer, "sources": sources, "model": ctx["settings"].generation_model, "chunks_used": len(ctx["search_results"])}



def chat_stream(message: str, history: list[dict] | None = None, top_k: int = 8, persona_id: str | None = None):
    """Generator que produz eventos SSE com tokens em tempo real.

    Fluxo:
    1. Envia metadados (sources) como primeiro evento
    2. Streama tokens da resposta do Gemini
    3. Envia evento [DONE] ao finalizar
    """
    ctx = _prepare_chat_context(message, history, top_k, persona_id=persona_id)

    # Envia sources como primeiro evento SSE
    sources = _build_sources(ctx["search_results"])
    meta_event = {
        "type": "meta",
        "sources": sources,
        "model": ctx["settings"].generation_model,
        "chunks_used": len(ctx["search_results"]),
    }
    yield f"data: {json.dumps(meta_event, ensure_ascii=False)}\n\n"

    # Streama tokens
    try:
        stream = ctx["client"].models.generate_content_stream(
            model=ctx["settings"].generation_model,
            contents=ctx["contents"],
            config=types.GenerateContentConfig(
                system_instruction=ctx["system_prompt"],
                temperature=ctx["temperature"],
                max_output_tokens=4096,
            ),
        )

        for chunk in stream:
            if chunk.text:
                token_event = {"type": "token", "content": chunk.text}
                yield f"data: {json.dumps(token_event, ensure_ascii=False)}\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_event = {"type": "error", "content": f"Erro ao gerar resposta: {e}"}
        yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    # Analytics
    latency_ms = (time.perf_counter() - ctx["start_time"]) * 1000
    scores = [r.get("score", 0) for r in ctx["search_results"]]
    avg_score = sum(scores) / len(scores) if scores else 0
    try:
        log_chat_event(
            query=message,
            rewritten_query=ctx.get("search_query"),
            intent=ctx.get("intent", "geral"),
            latency_ms=latency_ms,
            chunks_used=len(ctx["search_results"]),
            avg_score=avg_score,
            model=ctx["settings"].generation_model,
        )
    except Exception as e:
        logger.warning(f"Analytics log failed: {e}")

    # Sinaliza fim do stream
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
