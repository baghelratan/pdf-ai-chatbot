"""
Chat logic: retrieval → prompt → Gemini streaming response.
Uses the new google-genai SDK.
"""
from __future__ import annotations
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional

from google import genai
from google.genai import types

from config import GOOGLE_API_KEY, GEMINI_MODEL, MAX_HISTORY_TURNS
from vector_store import hybrid_search

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=GOOGLE_API_KEY)

_SYSTEM_PROMPT = """You are an expert document assistant. Your ONLY job is to answer questions \
based on the document excerpts provided below. Follow these rules strictly:

1. Answer ONLY from the provided excerpts. Never use outside knowledge.
2. Always cite the source: mention the filename and page number(s) in your answer.
3. If the answer is not found in the excerpts, say: "I couldn't find an answer to that in the uploaded documents."
4. Be concise, clear, and factual.
5. Use markdown formatting where helpful (bullet points, bold key terms, etc.).
"""


def _build_prompt(
    question: str,
    sources: List[Dict[str, Any]],
    history: List[Dict[str, str]],
) -> str:
    """Construct the full prompt with context, history, and question."""
    context_blocks = []
    for i, src in enumerate(sources, 1):
        context_blocks.append(
            f"[Excerpt {i} | File: {src['filename']} | Page: {src['page_number']}]\n"
            f"{src['text']}"
        )
    context = "\n\n---\n\n".join(context_blocks)

    # Last N turns of history
    recent = history[-(MAX_HISTORY_TURNS * 2):]
    history_text = ""
    if recent:
        turns = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            turns.append(f"{role}: {msg['content']}")
        history_text = "\n\nConversation History:\n" + "\n".join(turns)

    return (
        f"Document Excerpts:\n\n{context}"
        f"{history_text}"
        f"\n\nCurrent Question: {question}"
    )


async def stream_answer(
    question: str,
    doc_ids: Optional[List[str]],
    history: List[Dict[str, str]],
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Retrieve relevant chunks and stream a Gemini answer.

    Yields dicts:
        {"type": "sources", "data": [...]}
        {"type": "token",   "data": "..."}
        {"type": "done",    "data": ""}
        {"type": "error",   "data": "..."}
    """
    # 1. Retrieve
    sources = hybrid_search(question, doc_ids=doc_ids)

    if not sources:
        yield {
            "type": "error",
            "data": "No relevant content found in the uploaded documents.",
        }
        return

    # 2. Emit sources immediately
    yield {"type": "sources", "data": sources}

    # 3. Build prompt
    prompt = _build_prompt(question, sources, history)

    # 4. Stream from Gemini
    try:
        response = _client.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                temperature=0.2,
            ),
        )
        for chunk in response:
            if chunk.text:
                yield {"type": "token", "data": chunk.text}
    except Exception as exc:
        logger.error(f"Gemini error: {exc}")
        yield {"type": "error", "data": str(exc)}
        return

    yield {"type": "done", "data": ""}
