FROM python:3.12-slim AS base

WORKDIR /app

# System deps (gcc/g++ for native extensions, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install torch CPU-only first — avoids the 2 GB GPU wheel
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Dependency layer: cached until pyproject.toml changes.
# hatchling is configured to use the "app" package (see pyproject.toml),
# so a minimal stub satisfies its discovery at install time.
COPY pyproject.toml .
RUN mkdir -p app && touch app/__init__.py
RUN pip install --no-cache-dir ".[dev]"

# Copy real application code (overwrites the stub)
COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
