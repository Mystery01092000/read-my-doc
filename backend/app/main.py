import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Ask My Docs API",
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers — added incrementally per phase
    from app.auth.router import router as auth_router
    from app.documents.router import router as documents_router
    from app.chat.router import router as chat_router

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(documents_router, prefix="/documents", tags=["documents"])
    app.include_router(chat_router, prefix="/chat", tags=["chat"])

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
