# GitHub-Ready Repository Design
**Date:** 2026-04-09  
**Status:** Approved  
**Project:** read-my-doc (Ask My Docs)

---

## Overview

Prepare the `read-my-doc` repository for public GitHub release with full open-source community infrastructure, polished documentation, CI/CD automation, and a free-tier cloud deployment path.

**Decisions made:**
- License: MIT
- Screenshots: keep best 3–4 in `docs/screenshots/`, reference in README
- `.claude/` planning directory: excluded via `.gitignore`
- Approach: Full GitHub Ecosystem (Option C)
- Cloud deployment: Vercel (frontend) + Supabase (DB) + Upstash (Redis) + Render (API/workers) + Groq (LLM)

---

## Section 1: Root Cleanup & Core Files

### Delete from root
- All loose `*.png` screenshots (dev artifacts) — keep best 3–4 in `docs/screenshots/`
- `test_*.mjs` test scripts (dev artifacts)
- `sample_doc.txt`, `test-doc.txt`
- Any `node_modules/` at root level

### Add to root
- **`LICENSE`** — MIT License, 2026
- **`.gitignore`** — covers:
  - Python: `__pycache__/`, `.venv/`, `*.pyc`, `.pytest_cache/`, `*.egg-info/`, `dist/`, `htmlcov/`
  - Node: `node_modules/`, `dist/`, `.next/`, `*.tsbuildinfo`
  - Env: `.env`, `.env.*` (except `.env.example`)
  - IDE: `.vscode/`, `.idea/`, `*.swp`
  - macOS: `.DS_Store`
  - Internal: `.claude/`, `.agent/`, `.stitch/`, `.playwright-mcp/`
  - Dev artifacts: `*.png` (screenshots), `test_*.mjs`, `sc_*.png`, `sc*.png`
- **`.env.example`** — all env vars from README pre-filled with safe defaults, secrets as `CHANGE_ME`

---

## Section 2: README Enhancement

### Add at top
- Badges row: CI status, MIT license, Python 3.12, Docker, PRs Welcome
- Short screenshots grid (3–4 images): login → documents → upload modal → chat with citations

### Additions
- **Prerequisites block** in Quick Start: Docker 24+, Docker Compose v2, 8 GB RAM, `make`
- **Screenshots section** after intro blurb
- **Cloud Deployment section** linking to `docs/deployment/CLOUD.md`
- **Roadmap section** with 3–4 upcoming items (drawn from PRD)
- **Contributing section** linking to `CONTRIBUTING.md`
- **License footer**

### Keep unchanged
- Architecture diagram
- RAG Query Flow diagram
- Tech stack table
- Environment variables table
- Project structure tree
- Evaluation pipeline table
- Makefile commands table

---

## Section 3: GitHub Actions CI/CD Workflows

### `.github/workflows/ci.yml`
Triggers on push/PR to `main`:
- **Backend job**: `ruff` lint → `pytest` unit tests → `pytest` eval suite
- **Frontend job**: `npm run typecheck` → `npm run lint` → `npm run build`
- Jobs run in parallel; PR blocked if either fails

### `.github/workflows/docker-publish.yml`
Triggers on version tags (`v*.*.*`):
- Builds `backend` and `frontend` Docker images
- Pushes to GHCR as `ghcr.io/<owner>/read-my-doc-backend` and `ghcr.io/<owner>/read-my-doc-frontend`

### `.github/dependabot.yml`
- Weekly checks: Python deps (`/backend`), npm deps (`/frontend`), GitHub Actions
- Minor/patch updates grouped into single PR to reduce noise

---

## Section 4: GitHub Community Files

### `.github/CONTRIBUTING.md`
- Prerequisites & local dev setup
- Branch naming: `feat/`, `fix/`, `chore/`
- Commit message format (conventional commits)
- PR checklist: tests pass, eval gate passes, lint clean
- How to run eval suite locally

### `.github/ISSUE_TEMPLATE/`
- `bug_report.yml` — steps to reproduce, expected vs actual, environment details
- `feature_request.yml` — problem statement, proposed solution, alternatives
- `config.yml` — disables blank issues, links to Discussions for questions

### `.github/pull_request_template.md`
Checklist: description, linked issue, tests added, eval gate checked, screenshots for UI changes

### Root community files
- **`CHANGELOG.md`** — starts with `## [Unreleased]` and `## [1.0.0]` summary
- **`SECURITY.md`** — responsible disclosure policy, email placeholder, 90-day timeline
- **`CODE_OF_CONDUCT.md`** — Contributor Covenant v2.1

---

## Section 5: Cloud Deployment (Free Tier)

### Service map

| Service | Provider | Free Tier |
|---------|----------|-----------|
| Frontend | Vercel | Unlimited deploys, 100 GB bandwidth/mo |
| PostgreSQL + pgvector | Supabase | 500 MB DB, pgvector included |
| Redis | Upstash | 10K requests/day, 256 MB |
| FastAPI + Celery | Render | 750 hrs/mo (spins down after 15 min inactivity) |
| LLM | Groq | Free tier: Llama 3, Mixtral |

### Architecture change
`LLM_PROVIDER=groq` replaces Ollama for cloud deployments. Groq is OpenAI-compatible — generator needs only a base URL swap + API key (~5 lines in `generator.py`).

### Files added
- **`docs/deployment/CLOUD.md`** — step-by-step: Supabase → Upstash → Render → Vercel → Groq
- **`.github/workflows/deploy-vercel.yml`** — auto-deploy frontend on push to `main`
- **`.github/workflows/deploy-render.yml`** — trigger Render deploy hook on push to `main`
- **`vercel.json`** — SPA routing config for React Router
- **Groq support in `backend/app/rag/generator.py`** — `LLM_PROVIDER=groq` path
- **`.env.example`** updated with Groq variables

### Render caveat
Free tier spins down after 15 min inactivity → ~30s cold start. Documented in `CLOUD.md`. Upgrade to $7/mo paid plan to keep warm.

---

## File Manifest

```
read-my-doc/
├── LICENSE                                    # MIT
├── .gitignore                                 # comprehensive
├── .env.example                               # all vars, safe defaults
├── CHANGELOG.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── vercel.json
├── README.md                                  # enhanced
├── docs/
│   ├── screenshots/                           # 3-4 curated UI screenshots
│   └── deployment/
│       └── CLOUD.md                           # free tier deployment guide
├── .github/
│   ├── CONTRIBUTING.md
│   ├── pull_request_template.md
│   ├── dependabot.yml
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── feature_request.yml
│   │   └── config.yml
│   └── workflows/
│       ├── ci.yml
│       ├── docker-publish.yml
│       ├── deploy-vercel.yml
│       └── deploy-render.yml
└── backend/
    └── app/rag/generator.py                   # +Groq LLM_PROVIDER support
```

---

## Out of Scope
- Database schema changes
- Frontend feature changes
- Backend API changes (except Groq support in generator)
- Paid infrastructure setup
