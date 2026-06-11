"""
Pure-Python vector store using numpy cosine similarity + BM25 hybrid search.
No C++ compilation required — works on Windows without Visual C++ Build Tools.
Persists the index to disk as a pickle file.
"""
from __future__ import annotations
import os
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from rank_bm25 import BM25Okapi

from config import CHROMA_PERSIST_DIR, TOP_K, BM25_WEIGHT, VECTOR_WEIGHT
from embeddings import embed_texts, embed_query

logger = logging.getLogger(__name__)

# ── Persistence ───────────────────────────────────────────────────────────────
_INDEX_PATH = Path(CHROMA_PERSIST_DIR) / "vector_index.pkl"

# In-memory store
# Each entry: {chunk_id, doc_id, filename, page_number, chunk_index, text, embedding}
_store: List[Dict[str, Any]] = []


def _load_index() -> None:
    """Load persisted index from disk at startup."""
    global _store
    if _INDEX_PATH.exists():
        try:
            with open(_INDEX_PATH, "rb") as f:
                _store = pickle.load(f)
            logger.info(f"Loaded {len(_store)} chunks from disk index.")
        except Exception as exc:
            logger.warning(f"Could not load index: {exc}. Starting fresh.")
            _store = []


def _save_index() -> None:
    """Persist index to disk."""
    _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_INDEX_PATH, "wb") as f:
        pickle.dump(_store, f)


# Load on import
_load_index()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cosine_similarity(a: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between vector a and matrix B (rows = vectors)."""
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    B_norms = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-10)
    return B_norms @ a_norm


# ── Public API ────────────────────────────────────────────────────────────────

def add_chunks(chunks: List[Dict[str, Any]]) -> None:
    """Embed and store a list of chunk dicts."""
    if not chunks:
        return

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    for chunk, emb in zip(chunks, embeddings):
        _store.append(
            {
                "chunk_id":    chunk["chunk_id"],
                "doc_id":      chunk["doc_id"],
                "filename":    chunk["filename"],
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "text":        chunk["text"],
                "embedding":   np.array(emb, dtype=np.float32),
            }
        )

    _save_index()
    logger.info(f"Stored {len(chunks)} chunks. Total: {len(_store)}.")


def hybrid_search(
    query: str,
    doc_ids: Optional[List[str]] = None,
    k: int = TOP_K,
) -> List[Dict[str, Any]]:
    """
    Hybrid search: vector cosine similarity (70%) + BM25 keyword (30%).

    Args:
        query:   User question.
        doc_ids: Restrict to these document IDs. None = search all.
        k:       Number of top results to return.
    """
    if not _store:
        return []

    # Filter by doc_ids if provided
    pool = (
        [e for e in _store if e["doc_id"] in doc_ids]
        if doc_ids else _store
    )
    if not pool:
        return []

    # ── Vector similarity ─────────────────────────────────────────────────
    q_emb = np.array(embed_query(query), dtype=np.float32)
    matrix = np.stack([e["embedding"] for e in pool])  # (N, D)
    vector_scores = _cosine_similarity(q_emb, matrix)  # (N,)

    # ── BM25 keyword scores ───────────────────────────────────────────────
    tokenised = [e["text"].lower().split() for e in pool]
    bm25 = BM25Okapi(tokenised)
    bm25_raw = np.array(bm25.get_scores(query.lower().split()))
    bm25_max = bm25_raw.max() if bm25_raw.max() > 0 else 1.0
    bm25_scores = bm25_raw / bm25_max

    # ── Blend ─────────────────────────────────────────────────────────────
    combined = VECTOR_WEIGHT * vector_scores + BM25_WEIGHT * bm25_scores

    # Fetch top-k * 4 then re-sort (already computed above)
    top_indices = np.argsort(combined)[::-1][:k]

    results = []
    for idx in top_indices:
        entry = pool[idx]
        results.append(
            {
                "text":        entry["text"],
                "filename":    entry["filename"],
                "page_number": entry["page_number"],
                "chunk_index": entry["chunk_index"],
                "doc_id":      entry["doc_id"],
                "score":       round(float(combined[idx]), 4),
            }
        )
    return results


def delete_doc(doc_id: str) -> int:
    """Remove all chunks belonging to a document. Returns count deleted."""
    global _store
    before = len(_store)
    _store = [e for e in _store if e["doc_id"] != doc_id]
    deleted = before - len(_store)
    if deleted:
        _save_index()
        logger.info(f"Deleted {deleted} chunks for doc_id={doc_id}")
    return deleted


def get_chunk_count(doc_id: str) -> int:
    """Return number of chunks stored for a given doc_id."""
    return sum(1 for e in _store if e["doc_id"] == doc_id)
