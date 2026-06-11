"""
FastAPI application entry point.
"""
from __future__ import annotations
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import UPLOAD_DIR, CHROMA_PERSIST_DIR
from routes import upload as upload_router
from routes import chat as chat_router
from routes import documents as docs_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure required directories exist
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
    logger.info("✅ PDF AI Chatbot backend started (numpy vector store).")
    yield
    logger.info("🛑 Backend shutting down.")


app = FastAPI(
    title="PDF AI Chatbot",
    description="Upload PDFs and chat with their contents via Gemini.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routes ────────────────────────────────────────────────────────────────
app.include_router(upload_router.router, prefix="/api", tags=["upload"])
app.include_router(chat_router.router,   prefix="/api", tags=["chat"])
app.include_router(docs_router.router,   prefix="/api", tags=["documents"])


@app.get("/api/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "pdf-ai-chatbot"}


# ── Serve React frontend (must come AFTER all API routes) ─────────────────────
_STATIC_DIR = Path(__file__).parent / "static"

if _STATIC_DIR.exists():
    # Serve hashed assets (JS/CSS bundles)
    app.mount("/assets", StaticFiles(directory=_STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """Return index.html for all non-API paths (SPA client-side routing)."""
        index = _STATIC_DIR / "index.html"
        return FileResponse(index)
else:
    @app.get("/", tags=["root"])
    async def root():
        return {
            "service": "PDF AI Chatbot",
            "version": "1.0.0",
            "status": "running (no frontend built)",
            "docs": "/docs",
            "health": "/api/health",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
