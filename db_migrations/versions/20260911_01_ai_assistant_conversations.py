"""Persist bounded AI Assistant conversation transcripts."""

import sqlalchemy as sa
from alembic import op

revision = "20260911_01"
down_revision = "20260909_02"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_assistant_conversations",
        sa.Column("conversation_id", sa.String(120), primary_key=True),
        sa.Column("role", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "ai_assistant_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "conversation_id",
            sa.String(120),
            sa.ForeignKey(
                "ai_assistant_conversations.conversation_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("message_role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_ai_assistant_messages_conversation_id",
        "ai_assistant_messages",
        ["conversation_id"],
    )
    op.create_index(
        "ix_ai_assistant_messages_created_at",
        "ai_assistant_messages",
        ["created_at"],
    )


def downgrade():
    raise RuntimeError(
        "Downgrade would remove AI Assistant conversation history. Restore a verified compatible backup instead."
    )
