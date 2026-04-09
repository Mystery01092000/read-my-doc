from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://amd_user:amd_pass@localhost:5432/ask_my_docs"

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
    groq_model: str = "llama3-70b-8192"

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
