"""
chat.py — POST /api/chat — RAG Chat endpoint.
"""

import logging
from fastapi import APIRouter, HTTPException

from app.schemas.models import ChatRequest, ChatResponse
from app.services.chat_service import chat as rag_chat

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
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
