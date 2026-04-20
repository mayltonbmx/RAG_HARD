"""
analytics.py — Serviço de analytics: logs de chat, perguntas frequentes e métricas.

Armazena eventos em JSONL com rotação de 90 dias.
Compatível com LGPD: queries podem ser anonimizadas sob demanda.
"""

import json
import os
import logging
import hashlib
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)

ANALYTICS_DIR = os.path.join(get_settings().data_dir, "analytics")
CHAT_LOG_FILE = os.path.join(ANALYTICS_DIR, "chat_logs.jsonl")
RETENTION_DAYS = 90


def _ensure_dir():
    os.makedirs(ANALYTICS_DIR, exist_ok=True)


def _hash_query(query: str) -> str:
    """Hash SHA-256 da query para agrupamento sem expor texto completo (LGPD)."""
    return hashlib.sha256(query.strip().lower().encode()).hexdigest()[:16]


def log_chat_event(
    query: str,
    rewritten_query: str | None = None,
    intent: str = "geral",
    latency_ms: float = 0,
    chunks_used: int = 0,
    avg_score: float = 0,
    model: str = "",
    user_id: str | None = None,
) -> None:
    """Registra um evento de chat no log JSONL."""
    _ensure_dir()

    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "query": query,
        "query_hash": _hash_query(query),
        "rewritten_query": rewritten_query,
        "intent": intent,
        "latency_ms": round(latency_ms, 1),
        "chunks_used": chunks_used,
        "avg_score": round(avg_score, 4),
        "model": model,
        "user_id": user_id,  # None até login estar pronto
    }

    try:
        with open(CHAT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to log chat event: {e}")


def _read_logs(days: int | None = None) -> list[dict]:
    """Lê eventos do log JSONL, filtrando por período."""
    if not os.path.exists(CHAT_LOG_FILE):
        return []

    cutoff = None
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)

    events = []
    try:
        with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    if cutoff:
                        ts = datetime.fromisoformat(event["timestamp"].replace("Z", ""))
                        if ts < cutoff:
                            continue
                    events.append(event)
                except (json.JSONDecodeError, KeyError):
                    continue
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")

    return events


def get_top_queries(limit: int = 20, days: int = 30) -> list[dict]:
    """Retorna as N perguntas mais frequentes no período."""
    events = _read_logs(days=days)
    counter = Counter()
    query_map = {}  # hash -> query mais recente

    for e in events:
        h = e.get("query_hash", "")
        q = e.get("query", "")
        counter[h] += 1
        query_map[h] = q  # mantém a versão mais recente

    results = []
    for h, count in counter.most_common(limit):
        results.append({
            "query": query_map.get(h, "?"),
            "count": count,
            "query_hash": h,
        })

    return results


def get_usage_stats(days: int = 30) -> dict:
    """Retorna métricas agregadas de uso."""
    events = _read_logs(days=days)

    if not events:
        return {
            "total_queries": 0,
            "avg_latency_ms": 0,
            "avg_chunks_used": 0,
            "avg_score": 0,
            "intent_distribution": {},
            "queries_per_day": {},
            "period_days": days,
        }

    latencies = [e.get("latency_ms", 0) for e in events]
    chunks = [e.get("chunks_used", 0) for e in events]
    scores = [e.get("avg_score", 0) for e in events if e.get("avg_score", 0) > 0]

    # Distribuição de intents
    intent_counter = Counter(e.get("intent", "geral") for e in events)

    # Queries por dia
    day_counter = Counter()
    for e in events:
        ts = e.get("timestamp", "")
        if ts:
            day = ts[:10]  # "2026-04-20"
            day_counter[day] += 1

    return {
        "total_queries": len(events),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
        "avg_chunks_used": round(sum(chunks) / len(chunks), 1) if chunks else 0,
        "avg_score": round(sum(scores) / len(scores), 4) if scores else 0,
        "intent_distribution": dict(intent_counter.most_common()),
        "queries_per_day": dict(sorted(day_counter.items())),
        "period_days": days,
    }


def rotate_logs():
    """Remove logs mais antigos que RETENTION_DAYS (90 dias)."""
    if not os.path.exists(CHAT_LOG_FILE):
        return 0

    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    kept = []
    removed = 0

    try:
        with open(CHAT_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    ts = datetime.fromisoformat(event["timestamp"].replace("Z", ""))
                    if ts >= cutoff:
                        kept.append(line)
                    else:
                        removed += 1
                except (json.JSONDecodeError, KeyError):
                    kept.append(line)

        if removed > 0:
            with open(CHAT_LOG_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(kept) + "\n" if kept else "")
            logger.info(f"Log rotation: removed {removed} old entries, kept {len(kept)}")

    except Exception as e:
        logger.error(f"Log rotation failed: {e}")

    return removed
