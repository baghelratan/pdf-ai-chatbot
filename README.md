# 📄 PDF AI Chatbot

Ever wished you could just *talk* to your PDF instead of ctrl+F-ing through 80 pages? That's exactly what this does. Drop in a PDF (or several), ask questions in plain English, and get answers with the exact page they came from — powered by Google Gemini.

🔗 **Live demo:** https://pdf-ai-chatbot-production-8647.up.railway.app

![Tech Stack](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-blue?logo=google) ![Backend](https://img.shields.io/badge/Backend-FastAPI-green?logo=fastapi) ![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?logo=react) ![Deploy](https://img.shields.io/badge/Deploy-Railway-blueviolet?logo=railway)

---

## What it does

- **Upload any PDF** — drag and drop, up to 50 MB, multiple files at once
- **Ask questions in plain English** — no special syntax, just chat
- **Get answers with sources** — every response shows exactly which file and page it came from
- **Scanned PDFs? No problem** — OCR via Tesseract handles image-based PDFs too
- **Streaming responses** — answers appear word by word, like ChatGPT
- **Remembers your conversation** — keeps the last 6 turns of context so follow-up questions work naturally

---

## How it works (the interesting bits)

### Chunking
When you upload a PDF, the text gets split into overlapping chunks of ~1,200 characters. The overlap (200 chars) is important — it means a sentence that sits right at a chunk boundary doesn't get cut off and lost. Each chunk is tagged with its filename and page number so we always know where it came from.

### Embeddings
Each chunk gets converted into a 768-dimensional vector using Google's `gemini-embedding-001` model. The key trick here is using different *task types* for documents vs queries — `retrieval_document` when indexing, `retrieval_query` when searching. This directional embedding meaningfully improves how well matches get found.

### Retrieval
When you ask a question, it doesn't just do a simple similarity search. It runs a **hybrid search**:
1. Embed your question and find the top 20 semantically similar chunks (vector search)
2. Re-score those 20 chunks with BM25 keyword matching
3. Blend the scores: 70% vector + 30% keyword
4. Return the top 5 for the LLM to use

This combo handles both fuzzy questions ("what does the author conclude about X?") and precise lookups ("find section 4.2") better than either approach alone.

### Prompt design
The model is told to answer *only* from the provided excerpts and always cite the source. If the answer isn't in the documents, it says so instead of making something up. Chat history is injected as a rolling window so follow-up questions work without re-reading everything.

```
[Excerpt 1 | File: report.pdf | Page: 3]
<text>
---
[Excerpt 2 | File: report.pdf | Page: 7]
<text>

Conversation History:
User: <previous question>
Assistant: <previous answer>

Current Question: <your question>
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│          React + Vite (Frontend)                 │
│  drag-and-drop upload  •  streaming chat         │
│  source cards with excerpts  •  markdown render  │
└────────────────────┬────────────────────────────┘
                     │ HTTP / SSE
┌────────────────────▼────────────────────────────┐
│          FastAPI (Backend)                       │
│  PyMuPDF + OCR  •  chunking  •  embeddings      │
│  numpy vector store  •  BM25 hybrid search      │
│  Gemini 2.5 Flash (streaming)                   │
└─────────────────────────────────────────────────┘
```

The frontend is served as static files directly from FastAPI — no separate frontend server needed in production.

---

## Running locally

You'll need Python 3.11+, Node.js 20+, and a [Gemini API key](https://aistudio.google.com/apikey) (free tier works fine).

```bash
git clone https://github.com/baghelratan/pdf-ai-chatbot
cd pdf-ai-chatbot
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt

# Create your .env file
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

python main.py
# → http://localhost:8000
```

**Frontend** (in a separate terminal):
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

Then open http://localhost:5173, upload a PDF, and start asking questions.

---

## Docker

If you prefer containers:

```bash
export GOOGLE_API_KEY=your_key_here
docker compose up --build
# → http://localhost:3000
```

---

## Deploying to Railway

1. Push the repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. Railway picks up `railway.toml` automatically and uses `Dockerfile.backend`
4. In your service's **Variables** tab, add `GOOGLE_API_KEY` with your key
5. Hit deploy — you'll get a public URL in a couple minutes

The Dockerfile does a multi-stage build: first compiles the React frontend, then copies the built files into the Python image so everything runs from one service.

---

## API

The full interactive docs are at `/docs` on any running instance. Quick reference:

| Method | Endpoint | What it does |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/upload` | Upload one or more PDFs |
| `GET` | `/api/documents` | List uploaded documents |
| `DELETE` | `/api/documents/{id}` | Remove a document |
| `POST` | `/api/chat` | Ask a question (streams back SSE) |

Chat responses stream as Server-Sent Events:
```
data: {"type": "sources", "data": [{filename, page_number, text, score}]}
data: {"type": "token",   "data": "partial answer..."}
data: {"type": "done",    "data": ""}
```

---

## Configuration

Everything is configurable via environment variables. The defaults are sensible for most use cases.

| Variable | Default | What it controls |
|---|---|---|
| `GOOGLE_API_KEY` | — | **Required.** Your Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Which Gemini model to use |
| `EMBEDDING_MODEL` | `gemini-embedding-001` | Embedding model |
| `CHUNK_SIZE` | `1200` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K` | `5` | How many chunks to feed the LLM |
| `VECTOR_WEIGHT` | `0.7` | Vector score weight in hybrid search |
| `BM25_WEIGHT` | `0.3` | Keyword score weight |
| `MAX_HISTORY_TURNS` | `6` | Conversation turns kept in context |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max upload size |

---

## Project layout

```
pdf-ai-chatbot/
├── backend/
│   ├── main.py           # FastAPI app + serves frontend static files
│   ├── config.py         # All settings from environment variables
│   ├── pdf_processor.py  # PDF text extraction (PyMuPDF + OCR)
│   ├── chunker.py        # Recursive text splitter with overlap
│   ├── embeddings.py     # Gemini embeddings (batched)
│   ├── vector_store.py   # Numpy vector store + BM25 hybrid search
│   ├── chat.py           # Retrieval → prompt → Gemini streaming
│   └── routes/
│       ├── upload.py     # POST /api/upload
│       ├── chat.py       # POST /api/chat (SSE)
│       └── documents.py  # GET, DELETE /api/documents
├── frontend/
│   └── src/
│       ├── App.jsx           # Main app + SSE streaming client
│       ├── index.css         # Styles
│       └── components/       # UploadPanel, ChatWindow, MessageBubble, SourceCard
├── Dockerfile.backend    # Multi-stage: builds frontend + runs backend
├── Dockerfile.frontend   # Standalone frontend (nginx) for separate deploys
├── docker-compose.yml
├── railway.toml
└── nginx.conf
```

---

## License

MIT — do whatever you want with it.
