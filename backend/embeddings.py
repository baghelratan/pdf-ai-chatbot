"""
Google Embeddings using the new google-genai SDK.
Model: gemini-embedding-001 (successor to text-embedding-004).
Batches requests for efficiency.
"""
from __future__ import annotations
import logging
from typing import List

from google import genai
from google.genai import types

from config import GOOGLE_API_KEY, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=GOOGLE_API_KEY)
_BATCH_SIZE = 50


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of texts (document chunks) for storage.
    Returns a list of float vectors, one per input text.
    """
    if not texts:
        return []

    all_embeddings: List[List[float]] = []

    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        result = _client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        all_embeddings.extend([list(e.values) for e in result.embeddings])

    return all_embeddings


def embed_query(query: str) -> List[float]:
    """Embed a single query string using the retrieval_query task type."""
    result = _client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[query],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return list(result.embeddings[0].values)
