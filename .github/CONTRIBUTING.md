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
