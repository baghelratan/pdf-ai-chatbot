"""
Text chunking for PDF pages.

Strategy: Recursive character splitter.
  - Target chunk size: CHUNK_SIZE chars (≈800 tokens at ~1.5 chars/token)
  - Overlap:           CHUNK_OVERLAP chars to preserve cross-boundary context
  - Split order:       paragraph → sentence → word
"""
from __future__ import annotations
import re
import uuid
from typing import List, Dict, Any

from config import CHUNK_SIZE, CHUNK_OVERLAP


# Separators tried in order (paragraph, sentence, word)
_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]


def _split_text(text: str, size: int, overlap: int) -> List[str]:
    """Recursively split text using natural language separators."""
    if len(text) <= size:
        return [text] if text.strip() else []

    for sep in _SEPARATORS:
        if sep and sep in text:
            parts = text.split(sep)
            chunks: List[str] = []
            current = ""
            for part in parts:
                candidate = (current + sep + part) if current else part
                if len(candidate) > size and current:
                    chunks.append(current.strip())
                    # start next chunk with overlap
                    overlap_text = current[-overlap:] if overlap else ""
                    current = (overlap_text + sep + part) if overlap_text else part
                else:
                    current = candidate
            if current.strip():
                chunks.append(current.strip())
            return [c for c in chunks if c]

    # Fallback: hard split
    return [text[i: i + size] for i in range(0, len(text), size - overlap)]


def chunk_pages(
    pages: List[Dict[str, Any]],
    doc_id: str,
    filename: str,
) -> List[Dict[str, Any]]:
    """
    Convert extracted pages into overlapping text chunks with metadata.

    Returns a list of chunk dicts:
    {
        chunk_id:    str  (unique UUID),
        doc_id:      str,
        filename:    str,
        page_number: int,
        chunk_index: int,
        text:        str,
    }
    """
    all_chunks: List[Dict[str, Any]] = []
    global_idx = 0

    for page in pages:
        if not page["has_text"]:
            continue

        raw_chunks = _split_text(page["text"], CHUNK_SIZE, CHUNK_OVERLAP)

        for local_idx, chunk_text in enumerate(raw_chunks):
            if not chunk_text.strip():
                continue
            all_chunks.append(
                {
                    "chunk_id": str(uuid.uuid4()),
                    "doc_id": doc_id,
                    "filename": filename,
                    "page_number": page["page_number"],
                    "chunk_index": global_idx,
                    "text": chunk_text.strip(),
                }
            )
            global_idx += 1

    return all_chunks
