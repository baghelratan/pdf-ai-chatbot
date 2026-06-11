"""
POST /api/upload — Accept one or more PDF files, process them, return doc metadata.
"""
from __future__ import annotations
import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel

from config import MAX_UPLOAD_SIZE_MB, UPLOAD_DIR
from pdf_processor import extract_text_from_pdf
from chunker import chunk_pages
from vector_store import add_chunks, get_chunk_count

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory document registry (keyed by doc_id)
# In production this would be a DB table.
_documents: dict[str, dict] = {}

MAX_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024


class UploadedDoc(BaseModel):
    doc_id: str
    filename: str
    page_count: int
    chunk_count: int


class UploadResponse(BaseModel):
    documents: List[UploadedDoc]


@router.post("/upload", response_model=UploadResponse)
async def upload_pdfs(files: List[UploadFile] = File(...)):
    upload_path = Path(UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)

    uploaded: List[UploadedDoc] = []

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' is not a PDF.",
            )

        # Read and size-check
        content = await file.read()
        if len(content) > MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File '{file.filename}' exceeds {MAX_UPLOAD_SIZE_MB} MB limit.",
            )

        doc_id = str(uuid.uuid4())
        save_path = upload_path / f"{doc_id}.pdf"

        with open(save_path, "wb") as f:
            f.write(content)

        try:
            # Extract text
            pages = extract_text_from_pdf(save_path)
            page_count = len(pages)

            # Chunk
            chunks = chunk_pages(pages, doc_id=doc_id, filename=file.filename)

            # Embed + store
            add_chunks(chunks)
            chunk_count = get_chunk_count(doc_id)

            doc_info = {
                "doc_id": doc_id,
                "filename": file.filename,
                "page_count": page_count,
                "chunk_count": chunk_count,
                "path": str(save_path),
            }
            _documents[doc_id] = doc_info

            uploaded.append(UploadedDoc(**{k: v for k, v in doc_info.items() if k != "path"}))
            logger.info(
                f"Uploaded '{file.filename}' → {page_count} pages, {chunk_count} chunks"
            )
        except Exception as exc:
            logger.error(f"Failed to process '{file.filename}': {exc}", exc_info=True)
            # Clean up saved file on failure
            try:
                save_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process '{file.filename}': {str(exc)}",
            )

    return UploadResponse(documents=uploaded)


def get_all_documents() -> dict:
    return _documents
