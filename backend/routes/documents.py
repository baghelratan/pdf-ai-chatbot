"""
GET  /api/documents        — list all uploaded documents in session
DELETE /api/documents/{id} — remove a document from store
"""
from __future__ import annotations
import os
import logging
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from vector_store import delete_doc
from routes.upload import get_all_documents

logger = logging.getLogger(__name__)
router = APIRouter()


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    page_count: int
    chunk_count: int


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    docs = get_all_documents()
    return [
        DocumentInfo(**{k: v for k, v in d.items() if k != "path"})
        for d in docs.values()
    ]


@router.delete("/documents/{doc_id}", status_code=status.HTTP_200_OK)
async def remove_document(doc_id: str):
    docs = get_all_documents()
    if doc_id not in docs:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = docs[doc_id]
    deleted = delete_doc(doc_id)

    # Remove saved file
    try:
        if os.path.exists(doc["path"]):
            os.remove(doc["path"])
    except Exception as exc:
        logger.warning(f"Could not delete file {doc['path']}: {exc}")

    del docs[doc_id]
    return {"deleted": deleted, "doc_id": doc_id}
