import os
from dotenv import load_dotenv

load_dotenv()

# ── Gemini ────────────────────────────────────────────────────────────────────
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY environment variable is not set. "
        "Add it to your Railway service Variables tab before deploying."
    )

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1200"))       # characters
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))  # characters

# ── Retrieval ─────────────────────────────────────────────────────────────────
TOP_K: int = int(os.getenv("TOP_K", "5"))
BM25_WEIGHT: float = float(os.getenv("BM25_WEIGHT", "0.3"))   # hybrid blend
VECTOR_WEIGHT: float = float(os.getenv("VECTOR_WEIGHT", "0.7"))

# ── Vector Store (numpy-based, no C++ required) ──────────────────────────────
CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./vector_db")

# ── Upload ────────────────────────────────────────────────────────────────────
MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

# ── Chat history ──────────────────────────────────────────────────────────────
MAX_HISTORY_TURNS: int = int(os.getenv("MAX_HISTORY_TURNS", "6"))
