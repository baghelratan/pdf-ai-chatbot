# 📄 PDF AI Chatbot

A full-stack web application that lets you upload PDF documents and have a natural-language conversation with their contents, powered by **Google Gemini 1.5 Flash** and **ChromaDB**.

![Tech Stack](https://img.shields.io/badge/LLM-Gemini%201.5%20Flash-blue?logo=google) ![Vector DB](https://img.shields.io/badge/VectorDB-ChromaDB-orange) ![Backend](https://img.shields.io/badge/Backend-FastAPI-green?logo=fastapi) ![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?logo=react)

---

## ✨ Features

| Feature | Status |
|---|---|
| Upload PDFs up to 50 MB | ✅ |
| Multiple PDF support | ✅ |
| Text extraction (PyMuPDF) | ✅ |
| OCR for scanned PDFs (Tesseract) | ✅ |
| Semantic vector search (ChromaDB) | ✅ |
| Hybrid BM25 + vector search | ✅ |
| Streaming responses (SSE) | ✅ |
| Source attribution with page numbers | ✅ |
| Collapsible excerpt viewer | ✅ |
| Conversation memory (last 6 turns) | ✅ |
| Dark glassmorphism UI | ✅ |
| Docker Compose deployment | ✅ |
| Railway deployment config | ✅ |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│          Frontend (Vite + React)                 │
│  • Drag-and-drop upload    • Streaming chat      │
│  • Source cards            • Markdown rendering  │
└────────────────────┬────────────────────────────┘
                     │ HTTP / SSE
┌────────────────────▼────────────────────────────┐
│          Backend (FastAPI + Python)              │
│  • PDF ingestion   • PyMuPDF + OCR              │
│  • Chunking        • Google Embeddings          │
│  • ChromaDB        • BM25 reranking             │
│  • Gemini 1.5 Flash (streaming)                 │
└─────────────────────────────────────────────────┘
```

---

## 🧠 Technical Decisions

### Chunking Strategy
**Recursive character text splitter** with:
- **Chunk size**: 1,200 characters (~800 tokens)
- **Overlap**: 200 characters (~130 tokens)
- **Split order**: paragraph → sentence → word → character

This approach preserves natural language boundaries. The overlap prevents information loss at chunk edges — a question spanning two chunks still gets a coherent answer. Metadata (`filename`, `page_number`, `chunk_index`) is stored with each chunk for precise source attribution.

### Embedding Model
**`text-embedding-004`** (Google's latest general-purpose model):
- 768-dimensional dense vectors
- Distinct `task_type` for documents (`retrieval_document`) vs queries (`retrieval_query`) — this directional embedding significantly improves retrieval precision
- Batched embedding (up to 100 texts/call) for efficiency

### Prompt Design
```
System:
  You are an expert document assistant. Answer ONLY from the provided excerpts.
  Always cite the source filename and page number(s). If the answer is not in
  the excerpts, say so explicitly. Use markdown formatting.

Context:
  [Excerpt 1 | File: report.pdf | Page: 3]
  <text>
  ---
  [Excerpt 2 | File: report.pdf | Page: 7]
  <text>

Conversation History:
  User: <previous question>
  Assistant: <previous answer>

Current Question: <user question>
```

Key choices:
- **Grounding instruction**: "Answer ONLY from excerpts" prevents hallucination
- **Explicit citation requirement**: Forces the model to include page references
- **Rolling history**: Last 6 turns (configurable) maintain conversational context without token overflow
- **Markdown formatting**: Produces structured, readable responses

### Retrieval Approach
**Hybrid search** combining:
1. **Vector similarity** (70% weight): ChromaDB cosine similarity against `text-embedding-004` query embedding
2. **BM25 keyword matching** (30% weight): Sparse lexical scoring on the candidate pool

Workflow:
1. Embed user query with `retrieval_query` task type
2. Fetch top-20 candidates from ChromaDB (filtered by session doc_ids)
3. Re-score all 20 with BM25 on tokenized text
4. Blend scores: `0.7 × vector_score + 0.3 × bm25_score`
5. Return top-5 for context injection

This hybrid approach handles both semantic queries ("what does the author conclude?") and keyword queries ("find section 4.2") better than either method alone.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd "pdf ai chatbot"
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt

# Create .env file
echo "GOOGLE_API_KEY=your_key_here" > .env

# Start backend
python main.py
# → runs on http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# → runs on http://localhost:5173
```

### 4. Open the App

Visit **http://localhost:5173**, upload a PDF, and start chatting!

---

## 🐳 Docker Compose

```bash
# Set your API key
export GOOGLE_API_KEY=your_key_here

# Build and start both services
docker compose up --build

# App will be available at http://localhost:3000
```

---

## 🚢 Deploy to Railway

### Backend Service
1. Push your repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. Railway auto-detects `railway.toml` and uses `Dockerfile.backend`
5. Add environment variable: `GOOGLE_API_KEY=your_key_here`
6. Deploy — Railway provides a public URL (e.g. `https://pdf-chatbot-backend.up.railway.app`)

### Frontend Service
1. Add another service in the same Railway project
2. Set `Dockerfile.frontend` as the Dockerfile
3. Set build arg: `VITE_API_URL=https://your-backend-url.up.railway.app`
4. Update `vite.config.js` proxy target to match your Railway backend URL

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/upload` | Upload PDFs (multipart) |
| `GET` | `/api/documents` | List uploaded documents |
| `DELETE` | `/api/documents/{id}` | Remove a document |
| `POST` | `/api/chat` | Stream chat response (SSE) |

### Chat Request Body
```json
{
  "question": "What are the key findings?",
  "doc_ids": ["uuid-1", "uuid-2"],
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

### SSE Event Types
```
data: {"type": "sources", "data": [{filename, page_number, text, score}]}
data: {"type": "token",   "data": "partial answer text"}
data: {"type": "done",    "data": ""}
data: {"type": "error",   "data": "error message"}
data: [DONE]
```

---

## 📁 Project Structure

```
pdf ai chatbot/
├── backend/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Centralised config from .env
│   ├── pdf_processor.py  # PyMuPDF + OCR extraction
│   ├── chunker.py        # Recursive text splitter
│   ├── embeddings.py     # Google text-embedding-004
│   ├── vector_store.py   # ChromaDB + BM25 hybrid search
│   ├── chat.py           # Retrieval → Gemini streaming
│   ├── requirements.txt
│   └── routes/
│       ├── upload.py     # POST /api/upload
│       ├── chat.py       # POST /api/chat (SSE)
│       └── documents.py  # GET/DELETE /api/documents
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main shell + SSE client
│   │   ├── index.css         # Design system
│   │   └── components/
│   │       ├── UploadPanel.jsx
│   │       ├── ChatWindow.jsx
│   │       ├── MessageBubble.jsx
│   │       └── SourceCard.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── nginx.conf
├── railway.toml
└── README.md
```

---

## ⚙️ Configuration

All backend settings are via environment variables (`.env`):

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | **Required.** Gemini API key |
| `GEMINI_MODEL` | `gemini-1.5-flash` | LLM model name |
| `EMBEDDING_MODEL` | `models/text-embedding-004` | Embedding model |
| `CHUNK_SIZE` | `1200` | Max chars per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K` | `5` | Number of chunks retrieved |
| `VECTOR_WEIGHT` | `0.7` | Weight of vector score in hybrid search |
| `BM25_WEIGHT` | `0.3` | Weight of BM25 score |
| `MAX_HISTORY_TURNS` | `6` | Chat turns kept in context |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max PDF upload size |

---

## 📜 License

MIT
