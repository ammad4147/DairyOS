"""Atomic operational write receipts and canonical-journal projection outbox.

Revision ID: 20260909_01
Revises: 20260907_01
"""

import sqlalchemy as sa
from alembic import op

revision = "20260909_01"
down_revision = "20260907_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "operational_write",
        sa.Column("request_id", sa.String(160), primary_key=True),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "operational_projection_outbox",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.String(160), sa.ForeignKey("operational_write.request_id"), nullable=False),
        sa.Column("journal_id", sa.Integer(), sa.ForeignKey("event_journal.id"), nullable=False, unique=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("delivered_at", sa.DateTime()),
    )
    op.create_index("ix_operational_projection_outbox_request_id", "operational_projection_outbox", ["request_id"])
    op.create_index("ix_operational_projection_outbox_status", "operational_projection_outbox", ["status"])


def downgrade():
    op.drop_table("operational_projection_outbox")
    op.drop_table("operational_write")
