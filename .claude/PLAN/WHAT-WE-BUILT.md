# What We Built — Complete Explanation Guide
## Ask My Docs

**Version:** 1.0  
**Date:** 2026-04-04

---

This document explains **everything** that was implemented, why each piece exists, and how the parts connect. Start here if you're new to the codebase.

---

## The Big Picture

Ask My Docs is a **Retrieval-Augmented Generation (RAG)** application. RAG solves a specific problem:

> **Problem:** Large Language Models (LLMs) don't know about your private documents. You can't ask GPT about your internal report or your company's PDF. And even if you paste the whole document into the prompt, it's slow, expensive, and LLMs forget context in long documents.

> **Solution:** RAG — find the most relevant *fragments* of your document first, then feed only those fragments to the LLM as context. The LLM generates an answer grounded in those fragments.

The system we built goes further than basic RAG by using:
1. **Hybrid retrieval** — two search methods combined (not just one)
2. **Reranking** — a second AI pass to pick the best fragments
3. **Citation enforcement** — the LLM must prove which fragment supports each claim

---

## System Architecture

```
                        ┌────────────��────────────────────────┐
                        │          USER'S BROWSER             │
                        │                                      │
                        │  React 18 + Vite + TypeScript        │
                        │  • Login / Register                  │
                        ���  • Upload documents                  │
                        │  • Chat with documents               │
                        │  • View session history              │
                        └──────────────┬─────────��────────────┘
                                       │ HTTP / SSE
                        ┌──────────────▼──────────────────────┐
                        │         FastAPI (Python 3.12)        │
                        │                                      │
                        │  /auth/*       JWT authentication    │
                        │  /documents/*  File management       │
                        │  /chat/*       RAG pipeline + SSE    │
                        └──────┬─────────────────┬────────────┘
                               │                 │
               ┌───────────────▼───┐   ┌─────────▼──────────────┐
               │   PostgreSQL 16   │   │     Redis 7             │
               │   + pgvector      │   │                         │
               │                   │   │  • Celery task queue    │
               │  • Users          │   │  • Celery results       │
               │  • Documents      │   └─────────┬────────────���─┘
               │  • Chunks         │             │
               │    (+ embeddings) │   ┌─────────▼──────────────┐
               │    (+ tsvectors)  │   │    Celery Worker        │
               │  • Chat sessions  │   │                         │
               │  • Messages       │   │  Async document         │
               └──────────���────────┘   │  processing:            │
                                        │  parse → chunk →        │
               ┌───────────────────┐   │  embed → store          │
               │   Ollama (LLM)    │   └───────────��────────────┘
               │                   │
               │  mistral / llama3 │
               │  Generates cited  │
               │  answers          │
               └────────��──────────┘
```

---

## Part 1: Infrastructure (`docker-compose.yml`)

We use Docker Compose to run all services locally with a single command.

### What each service does

| Service | Port | Purpose |
|---------|------|---------|
| `db` | 5432 | PostgreSQL 16 with pgvector extension — stores all data including vector embeddings |
| `redis` | 6379 | Message broker for Celery task queue; also stores task results |
| `ollama` | 11434 | Local LLM server — runs Mistral or LLaMA models on your machine |
| `backend` | 8000 | FastAPI web server — handles all REST API requests |
| `worker` | — | Celery worker — processes uploaded documents asynchronously |
| `flower` | 5555 | Web dashboard for monitoring Celery tasks |
| `frontend` | 3000 | Nginx serving the React SPA + proxying `/api` calls to backend |

### Why separate backend and worker?

Document processing (parsing a 50-page PDF, computing 200 embeddings) can take 30–60 seconds. If we did this inside the web server, every web request would be blocked while that one user's document processed. By using a Celery worker, document processing happens in a completely separate process — the web server stays responsive for all users.

---

## Part 2: Database Schema

Five tables. Each has a clear purpose.

### `users`
Stores registered accounts. Email must be unique. Password is stored as a bcrypt hash (never plain text).

### `refresh_tokens`
JWT-based auth uses two tokens:
- **Access token** — short-lived (30 min), sent with every API request
- **Refresh token** — long-lived (30 days), stored hashed in this table, used to get new access tokens

The `revoked_at` column enables logout (we mark the refresh token as revoked, so it can't be reused).

### `documents`
One row per uploaded file. The `status` column tracks the document through its processing lifecycle: `pending` → `processing` → `ready` (or `failed`). The `storage_path` points to the file on disk.

### `chunks`
The most important table. Every document is split into chunks (~512 tokens each), and each chunk gets:
- `content` — the text of the chunk
- `embedding` — a 384-dimensional vector (pgvector type) representing the chunk's semantic meaning
- `tsv` — a PostgreSQL tsvector for full-text search (BM25)
- `page_number`, `section_heading` — metadata for citation display

The HNSW index on `embedding` makes vector search fast. The GIN index on `tsv` makes full-text search fast.

### `chat_sessions` + `chat_session_documents`
A session is a conversation. One session can span multiple documents. The join table `chat_session_documents` links sessions to the documents they're chatting about.

### `messages`
Every message in a session is stored here. The `citations` column is JSONB — it stores a list of citation objects:
```json
[{"chunk_id": "...", "document_id": "...", "filename": "report.pdf", "page": 3, "snippet": "The margin was..."}]
```

---

## Part 3: Authentication

### Registration and Login (`app/auth/`)

When a user registers:
1. We check the email isn't already taken (`ConflictError` if it is)
2. We hash the password with bcrypt (bcrypt is slow by design — makes brute-force attacks impractical)
3. We create the user record
4. We issue both an access token and a refresh token

When a user logs in:
1. We look up the user by email
2. We verify the password against the stored bcrypt hash
3. We issue new tokens

### JWT Tokens

The access token encodes:
```json
{"sub": "user-uuid", "exp": 1745000000, "type": "access"}
```

The backend verifies this on every protected request via the `get_current_user_id` dependency. No database lookup needed — the token is cryptographically signed.

### Refresh Token Rotation

Each time a refresh token is used, it's revoked and a new one is issued. This means:
- If someone steals a refresh token, they can only use it once before it's invalid
- Logout immediately invalidates the refresh token

---

## Part 4: Document Management

### Upload Flow

```
User uploads file
       │
       ▼
FastAPI endpoint validates:
  - File extension (pdf/txt/md/csv/xlsx/pptx only)
  - File size (≤ 50 MB)
       │
       ▼
File saved to disk at /data/uploads/{user_id}/{doc_id}.{ext}
       │
       ▼
Document record created in DB (status: "pending")
       │
       ▼
Celery task enqueued: process_document(document_id)
       │
       ▼ (returns immediately — 202 Accepted)
Frontend polls /documents/{id} every 5 seconds to watch status
```

### Document Processing Pipeline (Celery Worker)

```
process_document(document_id)
       │
       ▼
Set status → "processing"
       │
       ▼
Parse file → list of ParsedPage objects
  PDF:  pymupdf → text per page (with page numbers)
  PPTX: python-pptx → text per slide (with slide heading)
  XLSX: openpyxl → headers + rows per sheet
  TXT:  stdlib → single page
  CSV:  stdlib csv → batches of 50 rows per page
  MD:   custom → sections split by # headings
       │
       ▼
Chunk pages → list of TextChunk objects
  Recursive text splitter:
  - Target: 512 tokens (~2048 chars)
  - Overlap: 64 tokens (~256 chars)
  - Splits on: \n\n → \n → ". " → " " → chars
  Overlap ensures that no information is lost at chunk boundaries
       │
       ▼
Embed chunks in batches of 32
  BAAI/bge-small-en-v1.5 → 384-dimensional vector per chunk
  Vectors are normalized (unit length) — enables cosine similarity
       │
       ▼
Bulk insert Chunk records into PostgreSQL
       │
       ▼
UPDATE chunks SET tsv = to_tsvector('english', content)
  This builds the BM25 full-text search index
       │
       ▼
Set status → "ready"
```

---

## Part 5: The RAG Pipeline

This is the core of the system. When a user sends a message, four things happen:

### Step 1: Hybrid Retrieval (`app/rag/retriever.py`)

We search for relevant chunks using **two different methods simultaneously**:

**Vector search (semantic)**
- Embed the user's query with the same model used for chunks
- Find the top-20 chunks where the query vector is closest to the chunk vector (cosine similarity)
- This finds semantically similar content even if the exact words differ
- Example: query "revenue growth" finds chunks containing "sales increase"

**BM25 full-text search (keyword)**
- Run `plainto_tsquery('english', query)` against the chunks' `tsv` column
- This finds chunks containing the exact query words (with stemming and stop-word removal)
- Example: query "Q3 2024 revenue" finds chunks mentioning "Q3" and "revenue" specifically

**Why both?** Vector search is good at semantic similarity but can miss exact numbers, names, and technical terms. BM25 is good at exact matches but misses paraphrased content. Together they're much better than either alone.

**Fusion with RRF (Reciprocal Rank Fusion)**
The two methods return separate ranked lists. We merge them with RRF:

```
score(chunk) = 1/(60 + rank_in_vector_list) + 1/(60 + rank_in_bm25_list)
```

RRF is robust because it only uses *ranks*, not raw scores. Vector similarity (cosine, 0-1) and BM25 scores (arbitrary scale) can't be added directly — but ranks can. The constant 60 prevents high-rank results from dominating.

### Step 2: Cross-Encoder Reranking (`app/rag/reranker.py`)

The top-20 RRF candidates are re-scored by the cross-encoder:

- The **retriever** uses the query and chunk independently (fast, but less precise)
- The **cross-encoder** scores each `(query, chunk)` *pair jointly* — it reads both simultaneously
- This is much more accurate but too slow to run on thousands of chunks (that's why we only run it on 20 candidates)

Result: the top-5 highest-scoring chunks go to the LLM.

**Why this two-stage approach?**
- Fast retrieval narrows 100,000+ chunks down to 20 candidates
- Precise reranking picks the best 5 from those 20
- This gives quality close to running the cross-encoder on all chunks, at a fraction of the cost

### Step 3: Citation-Enforced Generation (`app/rag/generator.py`)

The top-5 chunks are assembled into a prompt:

```
System: You are a document Q&A assistant. Every claim must include [chunk:ID].
        Return JSON: {"answer": "...[chunk:abc123]...", "citations": [...]}

User:   Context:
        [chunk:abc123] report.pdf, Page 3
        The Q3 revenue was $42M, up 18% year-over-year.

        ---
        [chunk:def456] report.pdf, Page 7
        Operating costs decreased by 12% due to...

        Question: What was the Q3 revenue?
```

The LLM returns:
```json
{
  "answer": "Q3 revenue was $42M, an 18% increase year-over-year [chunk:abc123].",
  "citations": [{"chunk_id": "abc123", "quote": "Q3 revenue was $42M, up 18%"}]
}
```

**Citation validation (anti-hallucination):** After the LLM responds, we check every `chunk_id` in the citations list against the actual retrieved chunk IDs. Any ID the LLM invented that wasn't in the retrieved set is stripped. This prevents the LLM from citing sources that don't exist.

### Step 4: SSE Streaming (`app/chat/router.py`)

The answer streams to the browser word by word using Server-Sent Events:

```
Server → Browser:
data: {"type": "token", "content": "Q3 "}
data: {"type": "token", "content": "revenue "}
data: {"type": "token", "content": "was "}
...
data: {"type": "citations", "citations": [...]}
data: [DONE]
```

The frontend appends each token to a live preview as it arrives. When `[DONE]` arrives, the session is reloaded from the server to get the persisted message with full citation metadata.

---

## Part 6: Chat System

### Sessions

A **session** is a named conversation. When you create a session, you pick which documents to chat with — the RAG retriever only searches chunks from those documents. This means:
- Your questions are scoped to the documents you selected
- You can have multiple sessions on the same document (different conversations)
- You can chat across multiple documents in one session

### Auto-titling

After the first message in a session, the session title is updated to the first 80 characters of the user's question. This makes the session list in the sidebar readable.

### Message Persistence

Every message (both user and assistant) is saved to the `messages` table. The assistant message includes the full `citations` JSON. This means:
- You can reopen any old session and see the full conversation
- Citation chips are always available on old messages

---

## Part 7: Frontend Architecture

### Tech choices

**React 18 + Vite** — React for UI components, Vite for fast builds and dev server HMR.

**TypeScript strict mode** — all types declared. `any` is banned. API response shapes are typed in `src/types/index.ts`.

**Tailwind CSS** — utility classes instead of CSS files. No style conflicts, no dead CSS.

**Zustand** — tiny state management library (2 KB). Only used for auth tokens — everything else is local state.

**No React Query** — in v1, API calls are managed manually with `useEffect` + `useState`. Simple enough that the extra dependency isn't worth it.

### Key frontend flows

**Authentication flow:**
```
/login form → authApi.login() → setTokens() in zustand → navigate to /documents
RequireAuth wrapper → reads isAuthenticated() from store → redirects to /login if false
```

**Upload flow:**
```
Dropzone drag-and-drop → documentsApi.upload() → document appears with "pending" badge
useEffect with setInterval(5s) → polls /documents → badge updates as status changes
```

**Chat flow:**
```
User types → hits Enter → userMessage added to state → streaming starts
fetch() with ReadableStream → tokens append to streamingContent (live preview)
[DONE] received → loadSession() → messages replaced with server-persisted versions (with citations)
CitationChip clicked → modal opens showing filename, page number, and source snippet
```

**Session creation flow:**
```
"+ New Chat" button → modal opens → lists all "ready" documents
User checks documents → "Start Chat" → chatApi.createSession() → navigate to /chat/:id
```

---

## Part 8: Evaluation Pipeline

### Why automated evaluation?

RAG systems can silently degrade. If someone changes the prompt, tweaks the chunking, or upgrades the LLM, the answer quality might drop without any error being thrown. The CI eval pipeline catches this.

### What we measure

**Citation Accuracy (target ≥ 0.90)**
The fraction of returned citations whose `chunk_id` exists in the retrieved set. A score of 0.9 means at most 10% of citations are hallucinated. The `_strip_invalid_citations()` function enforces this at runtime — our test verifies this function works correctly.

**Faithfulness (target ≥ 0.80)**
The degree to which the answer is grounded in the provided context (not generated from the LLM's training knowledge). We use a token-overlap heuristic in the unit tests; a full RAGAS-based eval runs in integration mode.

### How CI uses it

The GitHub Actions workflow runs `pytest tests/eval/` on any PR that touches `backend/app/rag/**`. If citation accuracy < 0.90 or faithfulness < 0.80, the check fails and the PR cannot be merged.

### Golden dataset

`tests/eval/fixtures/golden.jsonl` — 5 manually written question/answer pairs with known source documents. These are simple but representative. Add more before deploying to production.

---

## Part 9: File Organization Summary

```
read-my-doc/
├── .claude/PLAN/               ← Planning documents (BRD, PRD, this file, etc.)
├── .github/workflows/ci.yml   ← GitHub Actions: lint + test + eval gate
├── docker-compose.yml         ← All services: postgres, redis, ollama, backend, worker, frontend
├── Makefile                   ← Shortcuts: make dev, make test, make eval, make migrate
├── .env.example               ← Copy to .env, fill in secrets
│
├── backend/
│   ├── pyproject.toml         ← Python dependencies (fastapi, sqlalchemy, celery, sentence-transformers, etc.)
│   ├── Dockerfile             ← Multi-stage Python build
│   ├── alembic/               ← Database migrations (schema history)
│   │   └── versions/
│   │       ├── 0001_*         ← users + refresh_tokens tables
│   │       ├── 0002_*         ← documents + chunks tables (pgvector + GIN)
│   │       └── 0003_*         ← chat_sessions + messages tables
│   │
│   ├── app/
│   │   ├── main.py            ← FastAPI app factory, CORS, router registration
│   │   ├── config.py          ← All settings via environment variables
│   │   ├── dependencies.py    ← get_current_user_id (auth guard for endpoints)
│   │   │
│   │   ├── common/
│   │   │   ├── database.py    ← SQLAlchemy async engine + session factory
│   │   │   ├── security.py    ← JWT encode/decode + bcrypt hashing
│   │   │   ├── exceptions.py  ← NotFoundError, UnauthorizedError, etc.
│   │   │   └── pagination.py  ← PaginatedResponse helper
│   │   │
│   │   ├── auth/              ← Register, login, refresh, logout
│   │   ├── documents/         ← Upload, CRUD, parser, chunker
│   │   ├── chat/              ← Sessions, messages, SSE endpoint
│   │   └── rag/               ← Embedder, retriever, reranker, generator
│   │
│   ├── tasks/
│   │   ├── worker.py          ← Celery app configuration
│   │   └── document_tasks.py  ← process_document task (parse→chunk→embed→store)
│   │
│   └── tests/
│       ├── conftest.py        ← Test fixtures (in-memory SQLite DB, test client)
│       ├── auth/              ← Auth endpoint tests
│       ├── documents/         ← Upload/parser/chunker tests
│       ├── rag/               ← Generator citation tests
│       └── eval/              ← CI-gated evaluation suite
│           └── fixtures/      ← Golden Q&A pairs + sample documents
│
└── frontend/
    ├── package.json           ← npm dependencies
    ├── vite.config.ts         ← Build config + dev proxy to backend
    ├── tailwind.config.ts     ← Color palette + dark mode config
    ├── nginx.conf             ← Production SPA + API proxy config
    ├── Dockerfile             ← Node builder → nginx runner
    └── src/
        ├── App.tsx            ← Route tree (public + protected + AppShell)
        ├── types/index.ts     ← All TypeScript interfaces
        ├── api/               ← Typed HTTP clients (auth, documents, chat)
        ├── store/             ← Zustand auth store (JWT tokens)
        ├── hooks/             ← useAuth, useDarkMode
        ├── components/        ← AppShell (layout with sidebar)
        └── features/
            ├── auth/          ← LoginPage, RegisterPage, RequireAuth
            ├── documents/     ← DocumentsPage (upload + list)
            ├── chat/          ← ChatPage + MessageBubble + CitationChip
            └── history/       ← SessionSidebar (session list + new chat modal)
```

---

## Part 10: What's NOT Built Yet

These features are explicitly out of scope for v1 and documented in the PRD:

| Feature | Reason not built |
|---------|-----------------|
| OCR for scanned PDFs | Needs `tesseract` — complex dep, add in Phase 7 |
| Axios refresh interceptor | Token auto-refresh on 401 — add before production |
| Toast notification system | Inline error banners are sufficient for MVP |
| Mobile responsive layout | Sidebar collapse at `md:` breakpoint |
| Document search/filter | Nice to have, not blocking |
| RAGAS integration eval | Full eval requires running LLM — CI uses lighter heuristics |
| File preview (PDF inline) | `pdfjs-dist` is large — worth adding for better UX |

---

## Quick Reference: Key Files to Understand

If you want to understand how the system works, read these files in order:

1. `backend/app/config.py` — all configuration
2. `backend/app/common/database.py` — how DB connections work
3. `backend/app/auth/service.py` — register/login logic
4. `backend/tasks/document_tasks.py` — the full processing pipeline
5. `backend/app/rag/retriever.py` — hybrid retrieval + RRF
6. `backend/app/rag/reranker.py` — cross-encoder reranking
7. `backend/app/rag/generator.py` — LLM call + citation enforcement
8. `backend/app/chat/service.py` — how it all connects (end-to-end RAG)
9. `frontend/src/features/chat/ChatPage.tsx` — frontend streaming
10. `frontend/src/api/chat.ts` — SSE fetch pattern
