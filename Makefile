.PHONY: dev dev-build stop logs migrate migrate-down migrate-new test test-cov lint format eval eval-integration pull-model clean

# ── Infrastructure ─────────────────────────────────────────────────────────────

dev:
	docker compose up --build

dev-detach:
	docker compose up -d --build

stop:
	docker compose down

logs:
	docker compose logs -f

# ── Database ───────────────────────────────────────────────────────────────────

migrate:
	cd backend && alembic upgrade head

migrate-down:
	cd backend && alembic downgrade -1

migrate-new:
	cd backend && alembic revision --autogenerate -m "$(MSG)"

# ── Testing ────────────────────────────────────────────────────────────────────

test:
	cd backend && pytest tests/ -v --ignore=tests/eval

test-cov:
	cd backend && pytest tests/ -v --ignore=tests/eval --cov=app --cov-report=html --cov-report=term-missing

# ── Evaluation Pipeline ────────────────────────────────────────────────────────
# Fast unit-level eval (no LLM / DB required) — used in CI gate

eval:
	@echo "Running RAG evaluation suite..."
	cd backend && pytest tests/eval/ -v --tb=short --no-header \
		-p no:cacheprovider \
		2>&1 | tee /tmp/eval-results.txt
	@echo ""
	@echo "Eval results saved to /tmp/eval-results.txt"

# Full integration eval with RAGAS (requires running services + LLM)
eval-integration:
	cd backend && EVAL_INTEGRATION=1 pytest tests/eval/ -v --tb=short -m integration

# ── Linting ────────────────────────────────────────────────────────────────────

lint:
	cd backend && ruff check app tasks tests && ruff format --check app tasks tests
	cd frontend && npm run typecheck && npm run lint

format:
	cd backend && ruff format app tasks tests && ruff check --fix app tasks tests

# ── Ollama Models ──────────────────────────────────────────────────────────────

pull-model:
	docker compose exec ollama ollama pull mistral

pull-model-llama:
	docker compose exec ollama ollama pull llama3.2

# ── Frontend ───────────────────────────────────────────────────────────────────

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

# ── Clean ──────────────────────────────────────────────────────────────────────

clean:
	docker compose down -v --remove-orphans
	cd frontend && rm -rf node_modules dist
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -name "*.pyc" -delete 2>/dev/null || true
	find backend -name ".coverage" -delete 2>/dev/null || true
	rm -rf backend/htmlcov
