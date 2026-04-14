from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://amd_user:amd_pass@localhost:5432/ask_my_docs"

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Normalize Supabase/Heroku-style postgres:// URLs to postgresql+asyncpg://.
        Appends ssl=require only for real external hosts (contain a dot, e.g. supabase.co).
        Docker service names (db, postgres) and localhost never get ssl=require.
        """
        import re

        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        # Only add SSL for real FQDNs — host has a dot (e.g. aws-0.pooler.supabase.com)
        # Docker service names (db, redis) and localhost have no dots in the host part
        host_match = re.search(r"@([^:/]+)", v)
        host = host_match.group(1) if host_match else ""
        is_external = "." in host and host not in ("127.0.0.1",)
        has_ssl = "ssl=" in v or "sslmode=" in v
        if is_external and not has_ssl:
            v += "&ssl=require" if "?" in v else "?ssl=require"
        return v

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-me-to-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # LLM
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "mistral"
    llm_provider: str = "ollama"  # or "openai"
    openai_api_key: str = ""

    # Groq (OpenAI-compatible, free tier at console.groq.com)
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"

    # Embeddings / Reranking
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    embedding_dim: int = 384

    # Retrieval params
    retrieval_top_k: int = 20   # candidates before reranking
    rerank_top_n: int = 5       # chunks sent to LLM

    # Storage
    upload_dir: str = "/data/uploads"
    max_upload_size_mb: int = 50

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
