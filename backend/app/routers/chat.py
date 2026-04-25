"""
chat.py — POST /api/chat — RAG Chat endpoint.
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.models import ChatRequest, ChatResponse
from app.services.chat_service import chat as rag_chat, chat_stream as rag_chat_stream

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        logger.info(f"Chat: '{req.message[:60]}...'")
        result = rag_chat(
            message=req.message,
            history=req.history,
            top_k=req.top_k,
            persona_id=req.persona_id,
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    """Endpoint SSE para streaming de resposta em tempo real."""
    try:
        logger.info(f"Chat stream: '{req.message[:60]}...'")
        return StreamingResponse(
            rag_chat_stream(
                message=req.message,
                history=req.history,
                top_k=req.top_k,
                persona_id=req.persona_id,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        logger.error(f"Chat stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
