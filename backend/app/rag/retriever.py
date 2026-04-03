"""Hybrid retriever: pgvector cosine similarity + tsvector BM25, fused via RRF."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.embedder import embed_query

# Reciprocal Rank Fusion constant (k=60 is standard)
_RRF_K = 60


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    filename: str
    content: str
    page_number: int | None
    section_heading: str | None
    rrf_score: float


async def retrieve(
    session: AsyncSession,
    query: str,
    document_ids: list[UUID],
    top_k: int = 20,
) -> list[RetrievedChunk]:
    """Return top_k chunks from the given documents using hybrid retrieval + RRF."""
    if not document_ids:
        return []

    query_embedding = embed_query(query)
    doc_ids_str = [str(d) for d in document_ids]

    # ── Vector search ────────────────────────────────────────────────────────
    vector_rows = await session.execute(
        text("""
            SELECT
                c.id AS chunk_id,
                c.document_id,
                d.filename,
                c.content,
                c.page_number,
                c.section_heading,
                ROW_NUMBER() OVER (ORDER BY c.embedding <=> CAST(:query_vec AS vector)) AS rank
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.document_id = ANY(CAST(:doc_ids AS uuid[]))
            ORDER BY c.embedding <=> CAST(:query_vec AS vector)
            LIMIT :top_k
        """),
        {
            "query_vec": str(query_embedding),
            "doc_ids": doc_ids_str,
            "top_k": top_k,
        },
    )
    vector_results = vector_rows.fetchall()

    # ── Full-text search ─────────────────────────────────────────────────────
    fts_rows = await session.execute(
        text("""
            SELECT
                c.id AS chunk_id,
                c.document_id,
                d.filename,
                c.content,
                c.page_number,
                c.section_heading,
                ROW_NUMBER() OVER (ORDER BY ts_rank(c.tsv, plainto_tsquery('english', :query)) DESC) AS rank
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.document_id = ANY(CAST(:doc_ids AS uuid[]))
              AND c.tsv @@ plainto_tsquery('english', :query)
            ORDER BY ts_rank(c.tsv, plainto_tsquery('english', :query)) DESC
            LIMIT :top_k
        """),
        {"query": query, "doc_ids": doc_ids_str, "top_k": top_k},
    )
    fts_results = fts_rows.fetchall()

    # ── RRF Fusion ───────────────────────────────────────────────────────────
    scores: dict[UUID, float] = {}
    chunk_meta: dict[UUID, tuple] = {}

    for row in vector_results:
        cid = UUID(str(row.chunk_id))
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (_RRF_K + row.rank)
        chunk_meta[cid] = (row.document_id, row.filename, row.content, row.page_number, row.section_heading)

    for row in fts_results:
        cid = UUID(str(row.chunk_id))
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (_RRF_K + row.rank)
        if cid not in chunk_meta:
            chunk_meta[cid] = (row.document_id, row.filename, row.content, row.page_number, row.section_heading)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    return [
        RetrievedChunk(
            chunk_id=cid,
            document_id=UUID(str(chunk_meta[cid][0])),
            filename=chunk_meta[cid][1],
            content=chunk_meta[cid][2],
            page_number=chunk_meta[cid][3],
            section_heading=chunk_meta[cid][4],
            rrf_score=score,
        )
        for cid, score in ranked
        if cid in chunk_meta
    ]
