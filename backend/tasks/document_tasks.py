"""Document processing Celery tasks: parse → chunk → embed → index."""

import asyncio
import uuid
from pathlib import Path

from tasks.worker import celery_app


@celery_app.task(bind=True, name="tasks.process_document", max_retries=3, default_retry_delay=30)
def process_document(self, document_id: str) -> dict:  # type: ignore[type-arg]
    """Parse, chunk, embed, and index a document. Runs in a Celery worker process."""
    try:
        asyncio.run(_process_document_async(document_id))
        return {"document_id": document_id, "status": "ready"}
    except Exception as exc:
        raise self.retry(exc=exc)


async def _process_document_async(document_id_str: str) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.config import settings
    from app.documents.chunker import chunk_pages
    from app.documents.models import Chunk
    from app.documents.parser import parse_file
    from app.documents.repository import DocumentRepository
    from app.rag.embedder import embed_texts

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    document_id = uuid.UUID(document_id_str)

    async with session_factory() as session:
        async with session.begin():
            repo = DocumentRepository(session)

            # Fetch document (no user_id filter — worker has full access)
            from sqlalchemy import select
            from app.documents.models import Document
            result = await session.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()

            if doc is None:
                return  # Document was deleted before processing started

            try:
                # Update status to processing
                await repo.set_status(document_id, "processing")

                # Parse
                pages = parse_file(Path(doc.storage_path), doc.file_type)
                page_count = max((p.page_number for p in pages if p.page_number), default=len(pages))

                # Chunk
                text_chunks = chunk_pages(pages)
                if not text_chunks:
                    await repo.set_status(document_id, "failed", error_message="No text extracted from document")
                    return

                # Embed in batches of 32
                texts = [c.content for c in text_chunks]
                embeddings: list[list[float]] = []
                batch_size = 32
                for i in range(0, len(texts), batch_size):
                    batch = texts[i : i + batch_size]
                    embeddings.extend(embed_texts(batch))

                # Persist chunks
                chunk_models = [
                    Chunk(
                        document_id=document_id,
                        chunk_index=tc.chunk_index,
                        content=tc.content,
                        embedding=emb,
                        page_number=tc.page_number,
                        section_heading=tc.section_heading,
                        token_count=tc.token_count,
                    )
                    for tc, emb in zip(text_chunks, embeddings)
                ]
                session.add_all(chunk_models)

                # Update tsvectors in a raw SQL call after flush
                await session.flush()
                await session.execute(
                    __import__("sqlalchemy", fromlist=["text"]).text(
                        "UPDATE chunks SET tsv = to_tsvector('english', content) "
                        "WHERE document_id = :doc_id"
                    ),
                    {"doc_id": document_id},
                )

                await repo.set_status(document_id, "ready", page_count=page_count)

            except Exception as exc:
                await repo.set_status(document_id, "failed", error_message=str(exc)[:500])
                raise

    await engine.dispose()
