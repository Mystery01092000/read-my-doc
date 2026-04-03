"""create documents and chunks tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])

    op.create_table(
        "chunks",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", sa.UUID(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),  # overridden below with vector type
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_heading", sa.String(512), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("tsv", sa.Text(), nullable=True),  # overridden below with tsvector type
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Use raw SQL for pgvector-specific column types
    op.execute(f"ALTER TABLE chunks ALTER COLUMN embedding TYPE vector({EMBEDDING_DIM}) USING NULL::vector({EMBEDDING_DIM})")
    op.execute("ALTER TABLE chunks ALTER COLUMN embedding SET NOT NULL")
    op.execute("ALTER TABLE chunks ALTER COLUMN tsv TYPE tsvector USING NULL::tsvector")

    # Indexes
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])
    op.execute("CREATE INDEX ix_chunks_tsv ON chunks USING GIN(tsv)")
    op.execute(f"CREATE INDEX ix_chunks_embedding ON chunks USING hnsw(embedding vector_cosine_ops)")


def downgrade() -> None:
    op.drop_table("chunks")
    op.drop_table("documents")
