"""add token_usage to messages and tokens_embedded to documents

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Per-message LLM + retrieval token breakdown
    op.add_column(
        "messages",
        sa.Column(
            "token_usage",
            sa.JSON(),
            nullable=True,
            comment=(
                "Token counts: {prompt_tokens, completion_tokens, total_tokens, "
                "embedding_tokens, rerank_tokens}"
            ),
        ),
    )

    # Total tokens embedded during document processing
    op.add_column(
        "documents",
        sa.Column(
            "tokens_embedded",
            sa.Integer(),
            nullable=True,
            comment="Sum of token_count across all chunks (set after processing completes)",
        ),
    )


def downgrade() -> None:
    op.drop_column("messages", "token_usage")
    op.drop_column("documents", "tokens_embedded")
