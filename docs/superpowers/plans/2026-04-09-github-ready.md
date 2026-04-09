# GitHub-Ready Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the `read-my-doc` repo into a polished, open-source-ready GitHub repository with MIT license, CI/CD, community files, free-tier cloud deployment docs, and Groq LLM support.

**Architecture:** All changes are additive — new files for GitHub infrastructure, minor additions to `config.py` + `generator.py` for Groq, screenshot curation, and root cleanup. No existing features are changed.

**Tech Stack:** GitHub Actions, Docker/GHCR, Vercel, Render, Supabase, Upstash, Groq API (OpenAI-compatible)

---

## File Map

### Create
- `LICENSE`
- `.gitignore`
- `.env.example`
- `CHANGELOG.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `vercel.json`
- `docs/screenshots/` — 4 curated UI screenshots
- `docs/deployment/CLOUD.md`
- `.github/CONTRIBUTING.md`
- `.github/pull_request_template.md`
- `.github/dependabot.yml`
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/feature_request.yml`
- `.github/ISSUE_TEMPLATE/config.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/docker-publish.yml`
- `.github/workflows/deploy-vercel.yml`
- `.github/workflows/deploy-render.yml`

### Modify
- `README.md` — badges, screenshots section, cloud deploy section, roadmap, contributing, license footer
- `backend/app/config.py` — add `groq_api_key`, `groq_base_url`
- `backend/app/rag/generator.py` — add Groq dispatch (`llm_provider == "groq"`)

### Delete from root
- All loose `*.png` / `sc*.png` screenshots
- `test_*.mjs`, `test-doc.txt`, `sample_doc.txt`

---

## Task 1: Root Cleanup

**Files:**
- Delete: all loose `*.png` at root
- Delete: `test_chat_flow.mjs`, `test_frontend.mjs`, `test_frontend2.mjs`, `test_full_flow.mjs`
- Delete: `sample_doc.txt`, `test-doc.txt`

- [ ] **Step 1: Remove dev artifact files**

```bash
cd /path/to/read-my-doc
rm -f 01-login-page.png 02-after-login.png 03-documents-page.png 04-documents-with-upload.png
rm -f sc1_login.png sc2_documents.png sc3_documents_loaded.png sc4_chat_init.png sc5_register.png
rm -f sc_01_documents.png sc_02_modal.png sc_03_doc_selected.png sc_03_selected.png
rm -f sc_04_chat.png sc_05_typed.png sc_06_response.png sc_07_register.png
rm -f sc_after_init_chat.png sc_chat_page.png sc_doc_page.png sc_final.png sc_register.png
rm -f test_chat_flow.mjs test_frontend.mjs test_frontend2.mjs test_full_flow.mjs
rm -f sample_doc.txt test-doc.txt
```

- [ ] **Step 2: Create curated screenshots folder and copy best 4**

```bash
mkdir -p docs/screenshots
# The 4 best screenshots were captured as sc_0N_ series
# Re-take or copy from git history — use these filenames:
# docs/screenshots/01-login.png
# docs/screenshots/02-documents.png
# docs/screenshots/03-upload-modal.png
# docs/screenshots/04-chat-response.png
```

> NOTE: If screenshots were already deleted from working tree, use `git show HEAD:sc_01_documents.png > docs/screenshots/02-documents.png` etc. to recover from git. The exact recovery commands are in Task 2.

- [ ] **Step 3: Verify root is clean**

```bash
ls *.png 2>/dev/null && echo "FAIL: pngs still present" || echo "OK: no loose pngs"
ls test_*.mjs 2>/dev/null && echo "FAIL: test scripts still present" || echo "OK: no test scripts"
```

Expected: both lines print `OK`.

---

## Task 2: Curate Screenshots

**Files:**
- Create: `docs/screenshots/01-login.png`
- Create: `docs/screenshots/02-documents.png`
- Create: `docs/screenshots/03-upload-modal.png`
- Create: `docs/screenshots/04-chat-response.png`

- [ ] **Step 1: Recover best screenshots from git history**

```bash
mkdir -p docs/screenshots
git show HEAD:sc1_login.png > docs/screenshots/01-login.png
git show HEAD:sc_01_documents.png > docs/screenshots/02-documents.png
git show HEAD:sc_02_modal.png > docs/screenshots/03-upload-modal.png
git show HEAD:sc_06_response.png > docs/screenshots/04-chat-response.png
```

- [ ] **Step 2: Verify all 4 files exist and are non-empty**

```bash
ls -lh docs/screenshots/
```

Expected: 4 files, each > 50 KB.

- [ ] **Step 3: Commit screenshots**

```bash
git add docs/screenshots/
git commit -m "docs: add curated UI screenshots"
```

---

## Task 3: .gitignore

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Create .gitignore**

Create `.gitignore` with this exact content:

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
env/
*.egg-info/
dist/
build/
.pytest_cache/
htmlcov/
.coverage
.ruff_cache/

# Node
node_modules/
dist/
.next/
*.tsbuildinfo
frontend/dist/

# Environment
.env
.env.*
!.env.example

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store
Thumbs.db

# Docker
*.tar

# Uploads / data
/data/
backend/uploads/

# Internal tooling
.claude/
.agent/
.stitch/
.playwright-mcp/

# Dev artifacts (test scripts, loose screenshots)
test_*.mjs
sc*.png
sc_*.png
[0-9][0-9]-*.png

# Logs
*.log
celery*.pid
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add comprehensive .gitignore"
```

---

## Task 4: MIT License

**Files:**
- Create: `LICENSE`

- [ ] **Step 1: Create LICENSE file**

Create `LICENSE` with this content (replace `<YOUR NAME>` with your actual name):

```
MIT License

Copyright (c) 2026 <YOUR NAME>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Commit**

```bash
git add LICENSE
git commit -m "chore: add MIT license"
```

---

## Task 5: .env.example

**Files:**
- Create: `.env.example`

- [ ] **Step 1: Create .env.example**

Create `.env.example`:

```dotenv
# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://amd_user:amd_pass@db:5432/ask_my_docs
POSTGRES_USER=amd_user
POSTGRES_PASSWORD=amd_pass
POSTGRES_DB=ask_my_docs

# ── Redis ──────────────────────────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── JWT (CHANGE THIS — generate with: openssl rand -hex 32) ───────────────────
JWT_SECRET_KEY=CHANGE_ME

# ── LLM Provider ──────────────────────────────────────────────────────────────
# Options: ollama | openai | groq
LLM_PROVIDER=ollama

# Ollama (default, self-hosted)
OLLAMA_BASE_URL=http://ollama:11434
LLM_MODEL=mistral

# OpenAI (optional — set LLM_PROVIDER=openai to use)
OPENAI_API_KEY=

# Groq (optional — set LLM_PROVIDER=groq to use; free tier available at console.groq.com)
GROQ_API_KEY=
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama3-70b-8192

# ── Embeddings / Reranking ────────────────────────────────────────────────────
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# ── Storage ───────────────────────────────────────────────────────────────────
UPLOAD_DIR=/data/uploads
MAX_UPLOAD_SIZE_MB=50

# ── App ───────────────────────────────────────────────────────────────────────
APP_ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "chore: add .env.example with all configuration variables"
```

---

## Task 6: Groq LLM Support

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/rag/generator.py`

- [ ] **Step 1: Add Groq settings to config.py**

In `backend/app/config.py`, add after the `openai_api_key` line:

```python
    # Groq (OpenAI-compatible, free tier at console.groq.com)
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama3-70b-8192"
```

- [ ] **Step 2: Add Groq dispatch in generator.py**

In `backend/app/rag/generator.py`, update `_call_llm` and `_stream_llm`:

```python
async def _call_llm(user_prompt: str) -> tuple[str, int, int]:
    """Returns (response_text, prompt_tokens, completion_tokens)."""
    if settings.llm_provider == "openai":
        return await _call_openai(user_prompt)
    if settings.llm_provider == "groq":
        return await _call_groq(user_prompt)
    return await _call_ollama(user_prompt)


async def _stream_llm(user_prompt: str) -> AsyncIterator[str | tuple[int, int]]:
    """Yields str tokens then a final (prompt_tokens, completion_tokens) tuple."""
    if settings.llm_provider == "openai":
        async for item in _stream_openai(user_prompt):
            yield item
    elif settings.llm_provider == "groq":
        async for item in _stream_groq(user_prompt):
            yield item
    else:
        async for item in _stream_ollama(user_prompt):
            yield item
```

- [ ] **Step 3: Add _call_groq and _stream_groq functions**

Add after the `# ── OpenAI` section in `generator.py`:

```python
# ── Groq (OpenAI-compatible) ──────────────────────────────────────────────────

async def _call_groq(user_prompt: str) -> tuple[str, int, int]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.groq_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


async def _stream_groq(user_prompt: str) -> AsyncIterator[str | tuple[int, int]]:
    total_content = ""
    prompt_tokens = 0
    completion_tokens = 0
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{settings.groq_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": True,
                "stream_options": {"include_usage": True},
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    if token := data["choices"][0]["delta"].get("content", ""):
                        total_content += token
                        yield token
                    if usage := data.get("usage"):
                        prompt_tokens = usage.get("prompt_tokens", 0)
                        completion_tokens = usage.get("completion_tokens", 0)
                except (json.JSONDecodeError, KeyError):
                    continue
    yield (
        prompt_tokens or estimate_tokens(SYSTEM_PROMPT + user_prompt),
        completion_tokens or estimate_tokens(total_content),
    )
```

- [ ] **Step 4: Verify no syntax errors**

```bash
cd backend && python -c "from app.rag.generator import generate_answer; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/app/rag/generator.py
git commit -m "feat: add Groq LLM provider support (OpenAI-compatible, free tier)"
```

---

## Task 7: README Enhancement

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace README.md with enhanced version**

Replace the full content of `README.md` with:

```markdown
# Ask My Docs

> Upload your documents. Ask questions. Get cited answers.

[![CI](https://github.com/Mystery01092000/read-my-doc/actions/workflows/ci.yml/badge.svg)](https://github.com/Mystery01092000/read-my-doc/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](docker-compose.yml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Mystery01092000/read-my-doc/blob/main/.github/CONTRIBUTING.md)

A full-stack, self-hosted document Q&A platform. Upload PDFs, Markdown, Excel, or PowerPoint files, then chat with them using natural language and receive answers with verified inline citations.

## Screenshots

| Login | Documents | Upload | Chat with Citations |
|-------|-----------|--------|---------------------|
| ![Login](docs/screenshots/01-login.png) | ![Documents](docs/screenshots/02-documents.png) | ![Upload](docs/screenshots/03-upload-modal.png) | ![Chat](docs/screenshots/04-chat-response.png) |

## Features

- **Multi-format upload** — PDF, TXT, Markdown, CSV, Excel, PowerPoint (up to 50 MB)
- **Hybrid retrieval** — BM25 (PostgreSQL tsvector) + vector search (pgvector) fused with Reciprocal Rank Fusion
- **Cross-encoder reranking** — top-20 candidates reranked with `ms-marco-MiniLM-L-6-v2`
- **Citation enforcement** — every answer includes verified inline citations with page/section references
- **Session history** — all conversations saved; revisit any session from the sidebar
- **CI-gated evaluation** — RAGAS faithfulness ≥ 0.8 and citation accuracy ≥ 0.9 enforced on PRs
- **Self-hosted** — runs entirely with `docker compose up`; Ollama for LLM, no external APIs required
- **Cloud-ready** — swap to Groq (free tier) for serverless deployment on Vercel + Render + Supabase

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24+ and Docker Compose v2
- 8 GB RAM (for Ollama LLM)
- `make`

```bash
# 1. Clone and copy env
git clone https://github.com/Mystery01092000/read-my-doc.git && cd read-my-doc
cp .env.example .env
# Edit .env — set JWT_SECRET_KEY to a long random secret

# 2. Start all services
make dev

# 3. Pull an LLM model (in a separate terminal)
make pull-model

# 4. Run database migrations
make migrate
```

Frontend: http://localhost:3000
API docs: http://localhost:8000/docs
Celery Flower: http://localhost:5555

## Architecture

```
Browser (React 18 + Vite + TypeScript)
    │
    ▼
FastAPI (Python 3.12) — REST API + SSE streaming
    ├── Auth     — JWT access/refresh tokens, bcrypt passwords
    ├── Documents — upload → Celery → parse → chunk → embed → pgvector
    └── Chat     — hybrid retrieve → cross-encoder rerank → Ollama/Groq → cited answer
    │
    ▼
PostgreSQL 16 + pgvector   Redis 7   Ollama (or Groq)
```

### RAG Query Flow

```
Question → embed → [pgvector cosine + tsvector BM25] → RRF merge → cross-encoder rerank → LLM → cited answer
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| Backend | Python 3.12, FastAPI, SQLAlchemy async |
| Database | PostgreSQL 16 + pgvector extension |
| BM25 | PostgreSQL tsvector + GIN index |
| Embeddings | BAAI/bge-small-en-v1.5 (sentence-transformers) |
| Reranker | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| LLM | Ollama (self-hosted) · Groq · OpenAI (configurable) |
| Task Queue | Celery + Redis |
| Migrations | Alembic |
| State | Zustand |

## Development

```bash
make test         # Run tests (excluding eval)
make test-cov     # Tests with HTML coverage report
make eval         # Run RAG evaluation suite
make lint         # Ruff + TypeScript checks
make format       # Auto-format backend code
make migrate-new MSG="add index"   # New Alembic migration
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `JWT_SECRET_KEY` | *(required)* | Secret for JWT signing |
| `LLM_PROVIDER` | `ollama` | `ollama` · `openai` · `groq` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API base URL |
| `LLM_MODEL` | `mistral` | Ollama model name |
| `GROQ_API_KEY` | *(optional)* | Required if `LLM_PROVIDER=groq` |
| `GROQ_MODEL` | `llama3-70b-8192` | Groq model name |
| `OPENAI_API_KEY` | *(optional)* | Required if `LLM_PROVIDER=openai` |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Sentence-transformers model |
| `RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Cross-encoder model |
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum file upload size |
| `UPLOAD_DIR` | `/data/uploads` | File storage directory |

See [`.env.example`](.env.example) for the full list with descriptions.

## Cloud Deployment (Free Tier)

Deploy without a local GPU using Vercel + Render + Supabase + Upstash + Groq — all free tiers.

See **[docs/deployment/CLOUD.md](docs/deployment/CLOUD.md)** for the step-by-step guide.

| Service | Provider | Free Tier |
|---------|----------|-----------|
| Frontend | Vercel | 100 GB bandwidth/mo |
| Database + pgvector | Supabase | 500 MB |
| Redis | Upstash | 10K req/day |
| Backend + Workers | Render | 750 hrs/mo |
| LLM | Groq | Rate-limited free tier |

## Project Structure

```
read-my-doc/
├── backend/
│   ├── app/
│   │   ├── auth/          # JWT auth (register, login, refresh, logout)
│   │   ├── documents/     # Upload, parse, chunk, embed pipeline
│   │   ├── chat/          # Sessions, messages, SSE streaming
│   │   ├── rag/           # Embedder, retriever, reranker, generator
│   │   └── common/        # DB, security, exceptions, pagination
│   ├── tasks/             # Celery workers (document processing)
│   ├── alembic/           # Database migrations
│   └── tests/
│       ├── auth/
│       ├── documents/
│       ├── chat/
│       ├── rag/
│       └── eval/          # RAG evaluation suite + golden fixtures
├── frontend/
│   └── src/
│       ├── features/      # auth, documents, chat, history
│       ├── api/           # typed API clients
│       ├── store/         # zustand auth store
│       └── hooks/
├── docs/
│   ├── screenshots/       # UI screenshots for README
│   └── deployment/        # Cloud deployment guide
└── docker-compose.yml
```

## Evaluation Pipeline

The CI pipeline runs `make eval` on every PR that touches `backend/app/rag/**`:

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Citation Accuracy | ≥ 0.90 | % of citations referencing valid retrieved chunks |
| Faithfulness | ≥ 0.80 | Answers grounded in retrieved context |

Tests in `backend/tests/eval/` run without requiring a live LLM — citation accuracy is validated through the post-processing logic directly, and faithfulness uses a heuristic token-overlap scorer.

## Roadmap

- [ ] **Multi-user document spaces** — shared workspaces with role-based access
- [ ] **Streaming citations** — show citation chips inline as the answer streams
- [ ] **Re-upload / versioning** — replace a document and preserve chat history
- [ ] **OpenAI embeddings option** — swap sentence-transformers for text-embedding-3-small

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](.github/CONTRIBUTING.md) before opening a PR.

## License

MIT — see [LICENSE](LICENSE) for details.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: enhance README with badges, screenshots, cloud deploy, roadmap"
```

---

## Task 8: Community Files

**Files:**
- Create: `CHANGELOG.md`
- Create: `SECURITY.md`
- Create: `CODE_OF_CONDUCT.md`

- [ ] **Step 1: Create CHANGELOG.md**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-04-09

### Added
- Full-stack document Q&A application (FastAPI + React + PostgreSQL + pgvector)
- Hybrid retrieval: BM25 (tsvector) + vector search (pgvector) with Reciprocal Rank Fusion
- Cross-encoder reranking with `ms-marco-MiniLM-L-6-v2`
- Citation enforcement — every answer includes verified inline citations
- JWT authentication (register, login, refresh token rotation)
- Celery-based async document processing pipeline
- Multi-format document support: PDF, TXT, Markdown, CSV, Excel, PowerPoint
- SSE streaming for real-time chat responses
- Session history with sidebar navigation
- CI-gated RAG evaluation (faithfulness ≥ 0.8, citation accuracy ≥ 0.9)
- Groq LLM provider support (free tier alternative to Ollama)
- Self-hosted deployment via Docker Compose
- Free-tier cloud deployment guide (Vercel + Render + Supabase + Upstash + Groq)
```

- [ ] **Step 2: Create SECURITY.md**

```markdown
# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅        |

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

To report a security issue, email **[your-email@example.com]** with:
- A description of the vulnerability
- Steps to reproduce
- Potential impact

You will receive a response within **48 hours** acknowledging your report.

We follow a **90-day responsible disclosure** timeline:
1. Vulnerability reported (Day 0)
2. Acknowledgement sent (within 48 hours)
3. Fix developed and tested (within 30 days for critical, 90 days for others)
4. Fix released and reporter credited (unless anonymity requested)
5. Public disclosure (after fix is available)

Thank you for helping keep Ask My Docs secure.
```

- [ ] **Step 3: Create CODE_OF_CONDUCT.md**

```markdown
# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, caste, color, religion, or sexual
identity and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming,
diverse, inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment:

* Demonstrating empathy and kindness toward other people
* Being respectful of differing opinions, viewpoints, and experiences
* Giving and gracefully accepting constructive feedback
* Accepting responsibility and apologizing to those affected by our mistakes
* Focusing on what is best not just for us as individuals, but for the overall community

Examples of unacceptable behavior:

* The use of sexualized language or imagery, and sexual attention or advances of any kind
* Trolling, insulting or derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information without explicit permission
* Other conduct which could reasonably be considered inappropriate in a professional setting

## Enforcement Responsibilities

Community leaders are responsible for clarifying and enforcing our standards of
acceptable behavior and will take appropriate and fair corrective action in
response to any behavior that they deem inappropriate, threatening, offensive, or harmful.

## Scope

This Code of Conduct applies within all community spaces, and also applies when
an individual is officially representing the community in public spaces.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the community leaders responsible for enforcement at
**[your-email@example.com]**.

All complaints will be reviewed and investigated promptly and fairly.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org),
version 2.1, available at https://www.contributor-covenant.org/version/2/1/code_of_conduct.html.
```

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md SECURITY.md CODE_OF_CONDUCT.md
git commit -m "docs: add CHANGELOG, SECURITY policy, and CODE_OF_CONDUCT"
```

---

## Task 9: GitHub Community Files

**Files:**
- Create: `.github/CONTRIBUTING.md`
- Create: `.github/pull_request_template.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/ISSUE_TEMPLATE/config.yml`

- [ ] **Step 1: Create CONTRIBUTING.md**

Create `.github/CONTRIBUTING.md`:

```markdown
# Contributing to Ask My Docs

Thank you for your interest in contributing! This document explains how to get set up, submit changes, and what we expect from contributors.

## Prerequisites

- Docker 24+ and Docker Compose v2
- Python 3.12 (for running backend tests locally without Docker)
- Node.js 20+ (for running frontend checks locally)
- `make`

## Local Development Setup

```bash
git clone https://github.com/Mystery01092000/read-my-doc.git
cd read-my-doc
cp .env.example .env
# Set JWT_SECRET_KEY in .env to a random string
make dev          # starts all services
make migrate      # runs DB migrations
make pull-model   # pulls the default Ollama model (~4 GB)
```

Frontend is at http://localhost:3000, API docs at http://localhost:8000/docs.

## Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feat/<short-description>` | `feat/streaming-citations` |
| Bug fix | `fix/<short-description>` | `fix/refresh-token-rotation` |
| Docs | `docs/<short-description>` | `docs/update-cloud-guide` |
| Chore | `chore/<short-description>` | `chore/bump-dependencies` |

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

<optional body>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

## Before Submitting a PR

1. **Run tests** — all must pass:
   ```bash
   make test
   ```

2. **Run the RAG eval gate** — faithfulness and citation thresholds must pass:
   ```bash
   make eval
   ```

3. **Run lint** — no errors allowed:
   ```bash
   make lint
   ```

4. **Add tests** for any new behavior. We aim for 80%+ coverage on the backend.

5. **Update `.env.example`** if you add new environment variables.

## PR Review Process

- All PRs require at least one approving review
- CI must be green (tests + eval + lint)
- Keep PRs focused — one feature/fix per PR
- Link the related issue in your PR description

## Getting Help

- Open a [GitHub Discussion](https://github.com/Mystery01092000/read-my-doc/discussions) for questions
- Open an [Issue](https://github.com/Mystery01092000/read-my-doc/issues) for bugs or feature requests
```

- [ ] **Step 2: Create PR template**

Create `.github/pull_request_template.md`:

```markdown
## Description

<!-- What does this PR do? Why? Link the related issue. -->

Closes #

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor
- [ ] Documentation
- [ ] CI/infrastructure

## Checklist

- [ ] Tests added / updated and passing (`make test`)
- [ ] RAG eval gate passing (`make eval`) — required if touching `backend/app/rag/**`
- [ ] Lint clean (`make lint`)
- [ ] `.env.example` updated if new env vars added
- [ ] Screenshots added below if this is a UI change

## Screenshots (if UI change)

<!-- Before / After screenshots here -->
```

- [ ] **Step 3: Create bug report issue template**

Create `.github/ISSUE_TEMPLATE/bug_report.yml`:

```yaml
name: Bug Report
description: Something isn't working as expected
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to report a bug! Please fill out the form below.

  - type: textarea
    id: description
    attributes:
      label: What happened?
      description: A clear description of the bug.
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Steps to reproduce
      description: Step-by-step instructions to reproduce the issue.
      placeholder: |
        1. Upload a PDF file
        2. Ask "What is..."
        3. See error
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected behavior
      description: What did you expect to happen?
    validations:
      required: true

  - type: dropdown
    id: llm_provider
    attributes:
      label: LLM Provider
      options:
        - Ollama (self-hosted)
        - Groq
        - OpenAI
    validations:
      required: true

  - type: input
    id: llm_model
    attributes:
      label: LLM Model
      placeholder: e.g. mistral, llama3-70b-8192, gpt-4o-mini

  - type: input
    id: docker_version
    attributes:
      label: Docker version
      placeholder: e.g. Docker 24.0.5

  - type: input
    id: os
    attributes:
      label: Operating System
      placeholder: e.g. macOS 14, Ubuntu 22.04

  - type: textarea
    id: logs
    attributes:
      label: Relevant logs
      description: Paste any relevant logs from `make logs` or the browser console.
      render: shell
```

- [ ] **Step 4: Create feature request issue template**

Create `.github/ISSUE_TEMPLATE/feature_request.yml`:

```yaml
name: Feature Request
description: Suggest an improvement or new feature
labels: ["enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for the suggestion! Please fill out the form below.

  - type: textarea
    id: problem
    attributes:
      label: What problem does this solve?
      description: A clear description of the problem or limitation you're experiencing.
      placeholder: I'm always frustrated when...
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Proposed solution
      description: Describe what you'd like to happen.
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
      description: Have you considered any alternative solutions?

  - type: dropdown
    id: area
    attributes:
      label: Area
      options:
        - RAG / Retrieval quality
        - Document parsing / ingestion
        - Chat / Streaming
        - Authentication
        - Frontend / UI
        - Deployment / Infrastructure
        - Other
    validations:
      required: true
```

- [ ] **Step 5: Create issue template config**

Create `.github/ISSUE_TEMPLATE/config.yml`:

```yaml
blank_issues_enabled: false
contact_links:
  - name: Ask a question
    url: https://github.com/Mystery01092000/read-my-doc/discussions
    about: Use GitHub Discussions for questions and general help
```

- [ ] **Step 6: Commit**

```bash
git add .github/CONTRIBUTING.md .github/pull_request_template.md .github/ISSUE_TEMPLATE/
git commit -m "docs: add CONTRIBUTING guide, PR template, and issue templates"
```

---

## Task 10: Dependabot Config

**Files:**
- Create: `.github/dependabot.yml`

- [ ] **Step 1: Create dependabot.yml**

```yaml
version: 2
updates:
  # Python backend dependencies
  - package-ecosystem: pip
    directory: /backend
    schedule:
      interval: weekly
      day: monday
    groups:
      minor-and-patch:
        update-types:
          - minor
          - patch
    labels:
      - dependencies
      - python

  # Node frontend dependencies
  - package-ecosystem: npm
    directory: /frontend
    schedule:
      interval: weekly
      day: monday
    groups:
      minor-and-patch:
        update-types:
          - minor
          - patch
    labels:
      - dependencies
      - javascript

  # GitHub Actions
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
      day: monday
    labels:
      - dependencies
      - github-actions
```

- [ ] **Step 2: Commit**

```bash
git add .github/dependabot.yml
git commit -m "ci: add Dependabot config for Python, npm, and Actions"
```

---

## Task 11: CI Workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create ci.yml**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    name: Backend (lint + test + eval)
    runs-on: ubuntu-latest

    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: amd_user
          POSTGRES_PASSWORD: amd_pass
          POSTGRES_DB: ask_my_docs_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U amd_user -d ask_my_docs_test"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 10

    env:
      DATABASE_URL: postgresql+asyncpg://amd_user:amd_pass@localhost:5432/ask_my_docs_test
      REDIS_URL: redis://localhost:6379/0
      JWT_SECRET_KEY: test-secret-key-for-ci
      LLM_PROVIDER: ollama
      OLLAMA_BASE_URL: http://localhost:11434

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: backend/pyproject.toml

      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[dev]"

      - name: Lint (ruff)
        run: |
          cd backend
          ruff check app tasks tests
          ruff format --check app tasks tests

      - name: Run migrations
        run: |
          cd backend
          alembic upgrade head

      - name: Unit tests
        run: |
          cd backend
          pytest tests/ -v --ignore=tests/eval -x

      - name: RAG eval gate
        run: |
          cd backend
          pytest tests/eval/ -v --tb=short

  frontend:
    name: Frontend (typecheck + lint + build)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Type check
        run: cd frontend && npm run typecheck

      - name: Lint
        run: cd frontend && npm run lint

      - name: Build
        run: cd frontend && npm run build
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions CI workflow (backend + frontend)"
```

---

## Task 12: Docker Publish Workflow

**Files:**
- Create: `.github/workflows/docker-publish.yml`

- [ ] **Step 1: Create docker-publish.yml**

```yaml
name: Publish Docker Images

on:
  push:
    tags:
      - "v*.*.*"

env:
  REGISTRY: ghcr.io
  BACKEND_IMAGE: ghcr.io/${{ github.repository_owner }}/read-my-doc-backend
  FRONTEND_IMAGE: ghcr.io/${{ github.repository_owner }}/read-my-doc-frontend

jobs:
  publish:
    name: Build and push Docker images
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata (backend)
        id: meta-backend
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.BACKEND_IMAGE }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Extract metadata (frontend)
        id: meta-frontend
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.FRONTEND_IMAGE }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta-backend.outputs.tags }}
          labels: ${{ steps.meta-backend.outputs.labels }}

      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: ${{ steps.meta-frontend.outputs.tags }}
          labels: ${{ steps.meta-frontend.outputs.labels }}
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/docker-publish.yml
git commit -m "ci: add Docker image publish workflow on version tags"
```

---

## Task 13: Vercel + Render Deploy Workflows

**Files:**
- Create: `vercel.json`
- Create: `.github/workflows/deploy-vercel.yml`
- Create: `.github/workflows/deploy-render.yml`

- [ ] **Step 1: Create vercel.json**

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    }
  ]
}
```

- [ ] **Step 2: Create deploy-vercel.yml**

```yaml
name: Deploy Frontend to Vercel

on:
  push:
    branches: [main]
    paths:
      - "frontend/**"
      - "vercel.json"

jobs:
  deploy:
    name: Deploy to Vercel
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./frontend
          vercel-args: "--prod"
```

- [ ] **Step 3: Create deploy-render.yml**

```yaml
name: Deploy Backend to Render

on:
  push:
    branches: [main]
    paths:
      - "backend/**"
      - "docker-compose.yml"

jobs:
  deploy:
    name: Trigger Render Deploy
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Trigger Render deploy hook
        run: |
          curl -fsSL -X POST "${{ secrets.RENDER_DEPLOY_HOOK_URL }}"
```

- [ ] **Step 4: Commit**

```bash
git add vercel.json .github/workflows/deploy-vercel.yml .github/workflows/deploy-render.yml
git commit -m "ci: add Vercel and Render deploy workflows"
```

---

## Task 14: Cloud Deployment Guide

**Files:**
- Create: `docs/deployment/CLOUD.md`

- [ ] **Step 1: Create CLOUD.md**

Create `docs/deployment/CLOUD.md`:

```markdown
# Free-Tier Cloud Deployment Guide

Deploy Ask My Docs to the cloud using entirely free tiers. This guide uses:

| Service | Provider | Purpose |
|---------|----------|---------|
| Frontend | [Vercel](https://vercel.com) | React SPA hosting |
| Database + pgvector | [Supabase](https://supabase.com) | PostgreSQL with pgvector |
| Redis | [Upstash](https://upstash.com) | Celery broker + result backend |
| Backend + Workers | [Render](https://render.com) | FastAPI + Celery |
| LLM | [Groq](https://console.groq.com) | Fast LLM inference (free tier) |

> **Note on Render free tier:** The free tier spins down after 15 minutes of inactivity, causing a ~30 second cold start on the first request. Upgrade to the $7/mo Starter plan to keep the service warm.

---

## Step 1: Supabase (PostgreSQL + pgvector)

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project (choose a region close to your users)
3. Go to **Settings → Database** and enable the `pgvector` extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Copy your **Connection string** from **Settings → Database → Connection string → URI**
   - Use the `Transaction pooler` URL for the app (port 6543)
   - Format: `postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
5. Set `DATABASE_URL` in your Render environment variables (Step 3)

---

## Step 2: Upstash (Redis)

1. Create a free account at [upstash.com](https://upstash.com)
2. Create a new **Redis** database (select a region)
3. Copy the **Redis URL** from the database details page
   - Format: `rediss://default:[password]@[host]:6379`
4. Set `REDIS_URL` in your Render environment variables (Step 3)

---

## Step 3: Groq (LLM)

1. Create a free account at [console.groq.com](https://console.groq.com)
2. Go to **API Keys** and create a new key
3. Note the key — you'll set `GROQ_API_KEY` in Render (Step 4)
4. The default model is `llama3-70b-8192` (fast, high quality)

---

## Step 4: Render (FastAPI + Celery)

1. Create a free account at [render.com](https://render.com)
2. Connect your GitHub account and select the `read-my-doc` repository

### Deploy the Backend API

3. Click **New → Web Service**
4. Select the `read-my-doc` repository
5. Configure:
   - **Name:** `read-my-doc-backend`
   - **Root Directory:** `backend`
   - **Runtime:** Docker
   - **Dockerfile path:** `backend/Dockerfile`
6. Set environment variables:
   ```
   DATABASE_URL=<your Supabase connection string>
   REDIS_URL=<your Upstash Redis URL>
   JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
   LLM_PROVIDER=groq
   GROQ_API_KEY=<your Groq API key>
   GROQ_MODEL=llama3-70b-8192
   CORS_ORIGINS=https://<your-vercel-domain>.vercel.app
   APP_ENV=production
   ```
7. After deploy, run migrations via the Render Shell:
   ```bash
   alembic upgrade head
   ```

### Deploy the Celery Worker

8. Click **New → Background Worker**
9. Same repository, same root directory
10. Set the same environment variables as the API
11. Override the start command: `celery -A tasks.celery_app worker --loglevel=info`

### Get the Deploy Hook URL

12. In your Render service settings → **Deploy Hooks**, create a hook
13. Copy the URL and add it as `RENDER_DEPLOY_HOOK_URL` in your GitHub repository secrets

---

## Step 5: Vercel (Frontend)

1. Create a free account at [vercel.com](https://vercel.com)
2. Click **Add New → Project** and import the `read-my-doc` repository
3. Configure:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Set environment variable:
   ```
   VITE_API_URL=https://<your-render-service>.onrender.com
   ```
5. Deploy

### Add GitHub Secrets for Auto-Deploy

6. In your Vercel project → **Settings → General**, copy the **Project ID** and **Org ID**
7. Generate a Vercel token at [vercel.com/account/tokens](https://vercel.com/account/tokens)
8. Add to your GitHub repository secrets:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

---

## Step 6: Verify Deployment

```bash
# Health check
curl https://<your-render-service>.onrender.com/health

# API docs
open https://<your-render-service>.onrender.com/docs
```

Visit your Vercel URL to use the application.

---

## Cost Summary (Free Tiers)

| Provider | Free Limits | Next Tier |
|----------|-------------|-----------|
| Vercel | 100 GB bandwidth/mo, unlimited deployments | $20/mo |
| Supabase | 500 MB database, 5 GB bandwidth | $25/mo |
| Upstash | 10,000 requests/day, 256 MB | $0.20/100K requests |
| Render | 750 hrs/mo (one service), 100 GB bandwidth | $7/mo per service |
| Groq | ~14,400 req/day on free tier | Pay-as-you-go |
```

- [ ] **Step 2: Commit**

```bash
git add docs/deployment/CLOUD.md
git commit -m "docs: add free-tier cloud deployment guide (Vercel + Render + Supabase + Upstash + Groq)"
```

---

## Task 15: Push to GitHub

- [ ] **Step 1: Verify remote is set**

```bash
git remote -v
```

If no remote exists:
```bash
git remote add origin https://github.com/Mystery01092000/read-my-doc.git
```

- [ ] **Step 2: Verify .gitignore is effective (no secrets or node_modules staged)**

```bash
git status --short
```

Verify the following are NOT listed:
- `.env` (only `.env.example` is ok)
- `node_modules/`
- `.claude/`
- Any `*.png` screenshots at root

- [ ] **Step 3: Push to GitHub**

```bash
git push -u origin main
```

- [ ] **Step 4: Verify CI triggers on GitHub**

Visit: `https://github.com/Mystery01092000/read-my-doc/actions`

Expected: CI workflow starts automatically within 30 seconds of push.

---

## Self-Review Against Spec

- ✅ MIT License — Task 4
- ✅ .gitignore (excludes .claude/, node_modules, .env, screenshots) — Task 3
- ✅ .env.example with Groq vars — Task 5
- ✅ Root cleanup (screenshots → docs/screenshots/, delete test scripts) — Tasks 1–2
- ✅ README: badges, screenshots, cloud deploy section, roadmap, contributing, license — Task 7
- ✅ CI workflow (backend: lint+test+eval, frontend: typecheck+lint+build) — Task 11
- ✅ docker-publish.yml (GHCR on version tags) — Task 12
- ✅ dependabot.yml (Python, npm, Actions) — Task 10
- ✅ CONTRIBUTING.md — Task 9
- ✅ Issue templates (bug, feature, config) — Task 9
- ✅ PR template — Task 9
- ✅ CHANGELOG.md — Task 8
- ✅ SECURITY.md — Task 8
- ✅ CODE_OF_CONDUCT.md — Task 8
- ✅ Groq support in generator.py + config.py — Task 6
- ✅ vercel.json — Task 13
- ✅ deploy-vercel.yml + deploy-render.yml — Task 13
- ✅ docs/deployment/CLOUD.md — Task 14
- ✅ Push to GitHub — Task 15
