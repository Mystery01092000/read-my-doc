# Models Setup Guide
## Downloading, Running, and Configuring AI Models

**Version:** 1.0  
**Date:** 2026-04-04

---

## Overview

Ask My Docs uses three AI models:

| Model | Role | Runtime | Size |
|-------|------|---------|------|
| `BAAI/bge-small-en-v1.5` | Text embedding (384-dim vectors) | sentence-transformers (Python) | ~130 MB |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | Cross-encoder reranking | sentence-transformers (Python) | ~80 MB |
| `mistral` (or `llama3.2`) | Answer generation | Ollama | ~4–7 GB |

The embedding and reranker models are downloaded automatically by `sentence-transformers` on first use. The LLM must be pulled manually into Ollama.

---

## 1. LLM — Ollama

### 1.1 What is Ollama?

Ollama is a local LLM server. It exposes an OpenAI-compatible REST API at `http://localhost:11434`. The backend calls Ollama to generate answers — no data leaves your machine.

### 1.2 Ollama starts automatically

The `docker-compose.yml` starts an Ollama container automatically:

```yaml
ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama    # models persisted across restarts
```

You only need to pull a model once — it's stored in the `ollama_data` Docker volume.

### 1.3 Pull a model (required before first chat)

```bash
# Option A — via Makefile (recommended)
make pull-model          # pulls mistral (~4 GB)
make pull-model-llama    # pulls llama3.2 (~2 GB, faster)

# Option B — directly into the container
docker compose exec ollama ollama pull mistral
docker compose exec ollama ollama pull llama3.2

# Option C — if running Ollama natively (not in Docker)
ollama pull mistral
```

### 1.4 Available models (recommended)

| Model | Pull command | Size | Best for |
|-------|-------------|------|---------|
| `mistral` | `ollama pull mistral` | 4.1 GB | Quality answers, good at following JSON format |
| `llama3.2` | `ollama pull llama3.2` | 2.0 GB | Faster, good for development |
| `llama3.1:8b` | `ollama pull llama3.1:8b` | 4.7 GB | Strong reasoning |
| `gemma2:2b` | `ollama pull gemma2:2b` | 1.6 GB | Smallest, fastest |
| `phi3:mini` | `ollama pull phi3:mini` | 2.3 GB | Microsoft model, efficient |

**Recommendation for development:** `llama3.2` (fast, small, good at JSON)  
**Recommendation for production quality:** `mistral` or `llama3.1:8b`

### 1.5 Verify Ollama is running

```bash
# Check the running container
docker compose ps ollama

# Test the API directly
curl http://localhost:11434/api/tags

# Expected output (after pulling mistral):
# {"models":[{"name":"mistral:latest","size":4109854720,...}]}
```

### 1.6 Switch LLM model

Edit `.env`:

```bash
LLM_MODEL=llama3.2        # change to any pulled model
```

Restart the backend:

```bash
docker compose restart backend worker
```

### 1.7 Use OpenAI instead (optional)

To use OpenAI's API instead of Ollama:

```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

Restart backend + worker. No changes to code needed — the generator checks `settings.llm_provider` at runtime.

---

## 2. Embedding Model — BAAI/bge-small-en-v1.5

### 2.1 What it does

Every document chunk and every user query is converted into a 384-dimensional vector. These vectors encode semantic meaning — similar content has similar vectors regardless of exact wording.

### 2.2 Download (automatic)

The model downloads automatically the first time the Celery worker or backend starts:

```python
# app/rag/embedder.py
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-small-en-v1.5")
# Downloads to ~/.cache/huggingface/hub/ on first run
```

**Download size:** ~130 MB  
**Cached at:** `~/.cache/huggingface/hub/` (inside the container: auto-mounted)

### 2.3 Pre-warm the model (optional)

To avoid the cold-start delay on the first document upload, pre-warm the model after the worker starts:

```bash
# Trigger a test embedding
docker compose exec worker python -c "
from app.rag.embedder import get_embedder
get_embedder()
print('Embedding model loaded OK')
"
```

### 2.4 Change the embedding model

To use a different embedding model, update `.env` and the dimension:

```bash
# .env
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Then update `app/documents/models.py` and the migration:

```python
EMBEDDING_DIM = 384   # must match the model's output dimension
```

**Warning:** Changing the embedding model requires re-processing all existing documents (their embeddings will be incompatible with the new model's vector space).

### 2.5 Alternative embedding models

| Model | Dim | Size | Notes |
|-------|-----|------|-------|
| `BAAI/bge-small-en-v1.5` | 384 | 130 MB | **Default** — best size/quality tradeoff |
| `BAAI/bge-base-en-v1.5` | 768 | 440 MB | Higher quality, requires dim change |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | 90 MB | Widely used, slightly lower quality |
| `sentence-transformers/all-mpnet-base-v2` | 768 | 420 MB | Highest quality, slow on CPU |
| `text-embedding-3-small` (OpenAI) | 1536 | API call | Best quality, costs money |

---

## 3. Reranker Model — cross-encoder/ms-marco-MiniLM-L-6-v2

### 3.1 What it does

After hybrid retrieval returns the top-20 candidate chunks, the cross-encoder scores each `(query, chunk)` pair jointly. This is more accurate than vector similarity because it considers the full context of both the query and the chunk together.

### 3.2 Download (automatic)

Also downloaded automatically by `sentence-transformers` on first use:

```python
# app/rag/reranker.py
from sentence_transformers import CrossEncoder
model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
# Downloads ~80 MB to HuggingFace cache
```

**Download size:** ~80 MB

### 3.3 Alternative reranker models

| Model | Size | Notes |
|-------|------|-------|
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | 80 MB | **Default** — fast, good quality |
| `cross-encoder/ms-marco-MiniLM-L-12-v2` | 130 MB | Higher quality, slower |
| `cross-encoder/ms-marco-electra-base` | 430 MB | Best quality, significant compute |
| `BAAI/bge-reranker-base` | 280 MB | Good alternative |

---

## 4. GPU Acceleration (Optional)

### 4.1 Ollama with GPU

If you have an NVIDIA GPU:

```yaml
# docker-compose.yml — add to ollama service
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

```bash
# Also requires nvidia-container-toolkit on the host
sudo apt install nvidia-container-toolkit
docker compose up ollama
```

### 4.2 sentence-transformers with GPU

Embedding and reranking use PyTorch. CUDA is used automatically if available.

The Docker image installs the CPU-only version of PyTorch by default (smaller). To enable GPU for the worker:

```dockerfile
# backend/Dockerfile — replace torch install
RUN pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### 4.3 Check if GPU is being used

```bash
docker compose exec worker python -c "
import torch
print('CUDA available:', torch.cuda.is_available())
print('Device count:', torch.cuda.device_count())
"
```

---

## 5. Model Storage & Caching

### 5.1 HuggingFace cache (embedding + reranker)

Inside the Docker container, models are cached at:
```
/root/.cache/huggingface/hub/
```

To persist this across container rebuilds, add a volume in `docker-compose.yml`:

```yaml
worker:
  volumes:
    - uploads_data:/data/uploads
    - hf_cache:/root/.cache/huggingface   # add this
    
volumes:
  hf_cache:     # add this
```

### 5.2 Ollama model storage

Ollama models are stored in the `ollama_data` volume:
```
ollama_data:/root/.ollama/models/
```

This persists across `docker compose down` (but not `docker compose down -v`).

### 5.3 Model download on first run

Full first-run download sequence:

```
docker compose up
    │
    ├── Postgres, Redis: start immediately
    │
    ├── Ollama: starts, but no model yet
    │   └── make pull-model → download mistral (~4 GB, 5-15 min on broadband)
    │
    ├── Backend: starts, imports sentence-transformers
    │   └── First /documents upload → downloads bge-small (~130 MB, ~30 sec)
    │
    └── Worker: starts, imports CrossEncoder
        └── First rerank call → downloads ms-marco-MiniLM (~80 MB, ~20 sec)
```

**Total first-run download: ~4.3 GB**

---

## 6. Verify Everything Works

```bash
# 1. Check all services running
docker compose ps

# 2. Check backend health
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"0.1.0"}

# 3. Check Ollama has a model
curl http://localhost:11434/api/tags | python3 -m json.tool

# 4. Test embedding model loads
docker compose exec worker python -c "
from app.rag.embedder import embed_query
vec = embed_query('hello world')
print(f'Embedding dim: {len(vec)}')   # should print 384
"

# 5. Test reranker model loads
docker compose exec worker python -c "
from app.rag.reranker import get_reranker
m = get_reranker()
print('Reranker loaded:', m.model.config.model_type)
"

# 6. Test LLM via Ollama
curl http://localhost:11434/api/generate \
  -d '{"model":"mistral","prompt":"Say hello","stream":false}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"
```

---

## 7. Troubleshooting

### "No model found" error in Ollama

```bash
# Ollama is running but no model pulled yet
make pull-model   # or: docker compose exec ollama ollama pull mistral
```

### Embedding download fails (network error inside container)

```bash
# Set HuggingFace mirror if behind a firewall
docker compose exec worker bash -c "
  export HF_ENDPOINT=https://hf-mirror.com
  python -c 'from sentence_transformers import SentenceTransformer; SentenceTransformer(\"BAAI/bge-small-en-v1.5\")'
"
```

### Ollama "connection refused" from backend

The backend uses `OLLAMA_BASE_URL=http://ollama:11434` inside Docker. If you see connection errors:
```bash
# Check Ollama container is healthy
docker compose logs ollama | tail -20
docker compose restart ollama
```

### Out of memory (embedding model)

If the worker crashes OOM when loading models:
```yaml
# docker-compose.yml — add memory limit
worker:
  mem_limit: 4g
```

### Slow first query

Cold start (first query after worker starts) loads all three models into memory. Subsequent queries reuse cached models (via `@lru_cache`). Pre-warm with:
```bash
docker compose exec worker python -c "
from app.rag.embedder import get_embedder
from app.rag.reranker import get_reranker
get_embedder(); get_reranker()
print('Models warm')
"
```
