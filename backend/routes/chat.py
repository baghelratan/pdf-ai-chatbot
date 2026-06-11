"""
POST /api/chat — Stream an answer with SSE (Server-Sent Events).
"""
from __future__ import annotations
import json
import logging
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from chat import stream_answer

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    doc_ids: Optional[List[str]] = None   # filter to specific docs
    history: List[ChatMessage] = []


async def _event_generator(request: ChatRequest):
    history = [m.model_dump() for m in request.history]

    async for event in stream_answer(
        question=request.question,
        doc_ids=request.doc_ids,
        history=history,
    ):
        yield f"data: {json.dumps(event)}\n\n"

    yield "data: [DONE]\n\n"


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(
        _event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
