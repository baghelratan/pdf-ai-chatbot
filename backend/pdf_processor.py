"""
PDF text extraction using PyMuPDF.
Falls back to pytesseract OCR for image-only pages.
"""
from __future__ import annotations
import io
import logging
from pathlib import Path
from typing import List, Dict, Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# ── Optional OCR support ───────────────────────────────────────────────────────
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.info("pytesseract / Pillow not installed – OCR disabled.")


def extract_text_from_pdf(file_path: str | Path) -> List[Dict[str, Any]]:
    """
    Extract text from every page of a PDF.

    Returns a list of dicts:
        [{page_number: int (1-based), text: str, has_text: bool}, ...]
    """
    file_path = Path(file_path)
    pages: List[Dict[str, Any]] = []

    doc = fitz.open(str(file_path))

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text("text").strip()

        # If the page has no selectable text, try OCR
        if not text and OCR_AVAILABLE:
            text = _ocr_page(page)
            logger.debug(f"Page {page_idx + 1}: OCR extracted {len(text)} chars")
        elif not text:
            logger.debug(f"Page {page_idx + 1}: no text, OCR not available")

        pages.append(
            {
                "page_number": page_idx + 1,
                "text": text,
                "has_text": bool(text),
            }
        )

    doc.close()
    return pages


def _ocr_page(page: fitz.Page) -> str:
    """Render a PDF page to image and run Tesseract OCR on it."""
    mat = fitz.Matrix(2.0, 2.0)  # 2× zoom for better OCR accuracy
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")

    image = Image.open(io.BytesIO(img_bytes))
    try:
        text = pytesseract.image_to_string(image, lang="eng")
        return text.strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"OCR failed: {exc}")
        return ""
