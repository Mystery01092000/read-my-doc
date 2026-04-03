# Implementation Plan
## Ask My Docs

**Version:** 1.0  
**Date:** 2026-04-04

---

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend | React 18 + Vite + TypeScript | SPA dashboard; no SSR needed; Vite is fast |
| Backend | Python 3.12 + FastAPI | Async, Pydantic validation, natural ML fit |
| Database | PostgreSQL 16 + pgvector | Single DB for metadata + vectors |
| BM25 | PostgreSQL tsvector + GIN index | No extra service; `ts_rank` for scoring |
| Embeddings | BAAI/bge-small-en-v1.5 (384-dim) | Strong quality/size ratio, runs on CPU |
| Cross-encoder | cross-encoder/ms-marco-MiniLM-L-6-v2 | Battle-tested, small enough for CPU |
| LLM | Ollama (mistral/llama3); OpenAI as env-switchable fallback | Self-hosted default |
| File parsing | pymupdf (PDF), python-pptx (PPT), openpyxl (XLSX), stdlib (TXT/CSV/MD) | No heavy deps |
| Task queue | Celery + Redis | Async doc processing with visibility |
| Auth | python-jose (JWT) + passlib[bcrypt] | Standard, no external auth service |
| Eval | RAGAS + pytest | Proven RAG evaluation framework |
| Migrations | Alembic | SQLAlchemy-native |
| State mgmt | Zustand | Minimal boilerplate |
| UI | Tailwind CSS + shadcn/ui | Rapid, consistent styling |

---

## Architecture

```
Browser (React SPA)
    │
    ▼
FastAPI REST API (port 8000)
    ├── Auth module ─────────── JWT access + refresh tokens
    ├── Documents module ────► Celery worker ──► Parse ──► Chunk ──► Embed ──► Store
    └── Chat module ─────────► Hybrid Retrieve ──► Rerank ──► LLM ──► Citations (SSE)
    │
    ▼
PostgreSQL 16 + pgvector    Redis 7    Ollama (LLM)
```

### RAG Query Flow

```
User question
    │
    ├──► Embed query (bge-small)
    │        │
    │   ┌────┴───────────────────────────┐
    │   │                                │
    │   ▼                                ▼
    │  pgvector cosine search         tsvector ts_rank search
    │  (top-20 by vector distance)    (top-20 by BM25 rank)
    │   │                                │
    │   └────────────┬───────────────────┘
    │                │
    │         RRF merge (top-20 unique)
    │                │
    │         Cross-encoder rerank
    │                │
    │         Top-5 chunks selected
    │                │
    │         LLM prompt + citation enforcement
    │                │
    │         Structured JSON output parsed
    │                │
    ▼         Citation IDs validated → stream to frontend
```

---

## Database Schema

### users
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
email       TEXT UNIQUE NOT NULL
password_hash TEXT NOT NULL
created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
```

### refresh_tokens
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
token_hash  TEXT NOT NULL
expires_at  TIMESTAMPTZ NOT NULL
revoked_at  TIMESTAMPTZ
created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
```

### documents
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
filename        TEXT NOT NULL
file_type       TEXT NOT NULL  -- pdf | txt | md | csv | xlsx | pptx
file_size_bytes BIGINT NOT NULL
storage_path    TEXT NOT NULL
status          TEXT NOT NULL DEFAULT 'pending'  -- pending | processing | ready | failed
error_message   TEXT
page_count      INT
created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
```

### chunks
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE
chunk_index     INT NOT NULL
content         TEXT NOT NULL
embedding       vector(384) NOT NULL
page_number     INT
section_heading TEXT
token_count     INT NOT NULL
tsv             TSVECTOR  -- GIN index
```
Indexes:
- `CREATE INDEX ON chunks USING gin(tsv)`
- `CREATE INDEX ON chunks USING hnsw(embedding vector_cosine_ops)`

### chat_sessions
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
title       TEXT NOT NULL DEFAULT 'New Chat'
created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
```

### chat_session_documents (join)
```sql
session_id  UUID REFERENCES chat_sessions(id) ON DELETE CASCADE
document_id UUID REFERENCES documents(id) ON DELETE CASCADE
PRIMARY KEY (session_id, document_id)
```

### messages
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
session_id  UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE
role        TEXT NOT NULL  -- user | assistant
content     TEXT NOT NULL
citations   JSONB NOT NULL DEFAULT '[]'
            -- [{chunk_id, document_id, filename, page, snippet}]
created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
```

---

## Directory Structure

```
read-my-doc/
├── docker-compose.yml
├── Makefile
├── .env.example
├── .gitignore
├── .github/workflows/ci.yml
├── .claude/PLAN/
│   ├── BRD.md
│   ├── PRD.md
│   └── IMPLEMENTATION.md  ← this file
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── app/
│   │   ├── main.py            # FastAPI app factory
│   │   ├── config.py          # Pydantic Settings
│   │   ├── dependencies.py    # DI: db session, current_user
│   │   ├── auth/
│   │   │   ├── models.py      # User, RefreshToken SQLAlchemy models
│   │   │   ├── schemas.py     # Pydantic request/response models
│   │   │   ├── repository.py  # DB queries (user CRUD, token management)
│   │   │   ├── service.py     # business logic (register, login, refresh)
│   │   │   └── router.py      # POST /auth/*
│   │   ├── documents/
│   │   │   ├── models.py      # Document, Chunk SQLAlchemy models
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   ├── router.py      # GET/POST/DELETE /documents/*
│   │   │   ├── parser.py      # File-type dispatch → text extraction
│   │   │   └── chunker.py     # Recursive text splitter
│   │   ├── chat/
│   │   │   ├── models.py      # ChatSession, Message SQLAlchemy models
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── router.py      # GET/POST/DELETE /chat/*
│   │   ├── rag/
│   │   │   ├── embedder.py    # sentence-transformers wrapper
│   │   │   ├── retriever.py   # hybrid search + RRF fusion
│   │   │   ├── reranker.py    # cross-encoder wrapper
│   │   │   ├── generator.py   # Ollama client + citation enforcement
│   │   │   └── prompts.py     # prompt templates
│   │   └── common/
│   │       ├── database.py    # async engine / session factory
│   │       ├── security.py    # JWT + bcrypt
│   │       ├── exceptions.py  # HTTP exception subclasses
│   │       └── pagination.py  # offset/limit helpers
│   ├── tasks/
│   │   ├── worker.py          # Celery app config
│   │   └── document_tasks.py  # parse → chunk → embed → index pipeline
│   └── tests/
│       ├── conftest.py
│       ├── test_health.py
│       ├── auth/
│       ├── documents/
│       ├── chat/
│       ├── rag/
│       └── eval/
│           ├── test_faithfulness.py
│           ├── test_citation_accuracy.py
│           └── fixtures/      # golden Q&A pairs + test docs
└── frontend/
    ├── package.json
    ├── Dockerfile
    ├── nginx.conf
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── types/index.ts     # all shared TypeScript types
        ├── api/client.ts      # axios instance factory
        ├── features/
        │   ├── auth/          # Login, Register pages + useAuth hook
        │   ├── documents/     # DocumentList, FileUpload, DocumentCard
        │   ├── chat/          # ChatView, MessageList, MessageBubble, CitationChip
        │   └── history/       # SessionSidebar
        ├── components/        # Button, Modal, Toast, Badge, Spinner
        ├── hooks/             # useDocuments, useChat, useSession
        ├── store/             # useAuthStore (zustand)
        └── types/
```

---

## Implementation Phases

### Phase 1: Project Skeleton & Infra ✅
- [x] Docker Compose (Postgres+pgvector, Redis, Ollama)
- [x] FastAPI app factory + health endpoint
- [x] Alembic setup
- [x] React + Vite + TypeScript + Tailwind scaffold
- [x] Makefile targets
- [x] GitHub Actions CI

### Phase 2: Authentication
- [ ] SQLAlchemy models: User, RefreshToken
- [ ] Alembic migration: create users + refresh_tokens tables
- [ ] Pydantic schemas: RegisterRequest, LoginRequest, TokenResponse
- [ ] Repository: create_user, get_by_email, create_refresh_token, revoke_refresh_token
- [ ] Service: register, login (bcrypt verify), refresh, logout
- [ ] Router: POST /auth/register, /login, /refresh, /logout
- [ ] Tests: register, login, refresh, logout, invalid token
- [ ] Frontend: LoginPage, RegisterPage, useAuthStore, route guards

### Phase 3: Document Management
- [ ] SQLAlchemy models: Document, Chunk
- [ ] Alembic migration: documents + chunks tables (pgvector + GIN indexes)
- [ ] Parser: pymupdf (PDF), python-pptx (PPT), openpyxl (XLSX), stdlib (TXT/CSV/MD)
- [ ] Chunker: recursive split (~512 tokens, 64 overlap)
- [ ] Embedder: preload bge-small on startup
- [ ] Celery task: process_document (parse → chunk → embed → store)
- [ ] Repository + Service + Router for documents CRUD
- [ ] Tests: upload, list, delete, status tracking, parser edge cases
- [ ] Frontend: FileUpload dropzone, DocumentList, DocumentCard with status badge

### Phase 4: RAG Chat Pipeline
- [ ] Retriever: pgvector cosine + tsvector ts_rank → RRF merge
- [ ] Reranker: cross-encoder scoring
- [ ] Generator: Ollama client, citation-enforcing prompt, Pydantic output validation
- [ ] Citation post-processing: validate chunk IDs, strip hallucinated ones
- [ ] SSE streaming endpoint for /chat/sessions/{id}/messages
- [ ] Chat sessions + messages repository + service + router
- [ ] Tests: retriever, reranker, generator (mocked LLM), SSE streaming
- [ ] Frontend: ChatView, MessageBubble, CitationChip, CitationDrawer, DocumentPicker

### Phase 5: History & Polish
- [ ] Session list sidebar with search
- [ ] Auto-title generation (LLM call after first message)
- [ ] Multi-document sessions
- [ ] Loading states, error toasts, empty states
- [ ] Responsive layout, dark mode toggle

### Phase 6: Evaluation Pipeline & CI Gate
- [ ] Golden test dataset (20-30 Q&A pairs) in tests/eval/fixtures/golden.jsonl
- [ ] Test documents in tests/eval/fixtures/docs/
- [ ] RAGAS metrics: faithfulness, answer relevance, context precision
- [ ] Custom citation accuracy metric
- [ ] pytest eval suite with threshold assertions
- [ ] CI job gates on faithfulness ≥ 0.8 and citation_accuracy ≥ 0.9

---

## Key Design Decisions

### Why PostgreSQL tsvector over Elasticsearch for BM25?
Eliminates a separate service, reducing operational complexity. tsvector with GIN index provides solid BM25-equivalent ranking via `ts_rank`. Elasticsearch adds value at >1M chunks — unnecessary at MVP scale.

### Why pgvector over Qdrant/ChromaDB?
Keeps the vector index co-located with document metadata, enabling JOIN-based user isolation (`WHERE chunks.document_id IN (SELECT id FROM documents WHERE user_id = ?)`). No separate vector service to manage.

### Why Celery + Redis over FastAPI BackgroundTasks?
BackgroundTasks shares the web server process — large model inference (embedding) would block request handling. Celery gives a separate worker process pool, task retry logic, and Flower for visibility.

### Why RRF (Reciprocal Rank Fusion) over weighted score combination?
RRF is score-scale-agnostic — vector similarity (cosine, 0-1) and BM25 scores have different ranges. RRF only uses rank positions, making it robust without requiring normalization tuning.

### Citation Enforcement Strategy
The LLM is prompted to return a structured JSON object:
```json
{
  "answer": "The margin was 42% in Q3 [chunk:abc123].",
  "citations": [
    {"chunk_id": "abc123", "quote": "Q3 margin reached 42%"}
  ]
}
```
Post-processing: every `chunk_id` in `citations` is validated against the retrieved chunk IDs. Unrecognized IDs are stripped. The frontend renders `[chunk:abc123]` as a clickable `CitationChip`.
